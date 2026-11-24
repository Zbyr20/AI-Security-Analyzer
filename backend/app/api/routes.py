from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scanner.security_scanner import SecurityScanner
from app.ai.ai_service import AIService
from app.validators.url_validator import URLValidator
from app.validators.target_guard import BlockedTargetError, TargetGuard

router = APIRouter()
scanner = SecurityScanner()
ai_service = AIService()
validator = URLValidator()
target_guard = TargetGuard()

class ScanRequest(BaseModel):
    url: str

@router.post("/scan")
def scan_website(request: ScanRequest):

    # Kullanıcı hatası (geçersiz URL) → 400; sunucu tarafı hata → 500.
    try:
        validated_url = validator.validate(request.url)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    # SSRF koruması: iç ağ / localhost / bulut metadata adresleri taranmaz.
    try:
        target_guard.check(validated_url)
    except BlockedTargetError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    try:
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