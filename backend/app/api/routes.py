from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scanner.security_scanner import SecurityScanner
from app.ai.ai_service import AIService
from app.validators.url_validator import URLValidator

router = APIRouter()
scanner = SecurityScanner()
ai_service = AIService()
validator = URLValidator()

class ScanRequest(BaseModel):
    url: str

@router.post("/scan")
def scan_website(request: ScanRequest):

    try:
        validated_url = validator.validate(request.url)

        security_result = scanner.scan(validated_url)
        security_data = security_result.to_dict()

        report = ai_service.generate_security_report(security_data)

        return {
            "url": validated_url,
            "scan": security_data,
            "report": report,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )