from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scanner.security_scanner import SecurityScanner
from app.ai.ai_service import AIService

router = APIRouter()
scanner = SecurityScanner()
ai_service = AIService()

class ScanRequest(BaseModel):
    url: str

@router.post("/scan")
def scan_website(request: ScanRequest):

    try: 
        # 1. güvenlik taraması
        security_result = scanner.scan(request.url)
        # 2. AI'ın kullanacağı dict
        security_data = security_result.to_dict()
        # 3. AI raporu 
        report = ai_service.generate_security_report(
            security_data
        )
        # 4.frontende dönen veri
        return {
            "url": request.url,
            "scan": security_data,
            "report":report
        }
    except Exception as e:
        raise HTTPException(
            status_code= 500,
            detail=str(e)
        )