from app.scanner.security_scanner import SecurityScanner
from app.ai.ai_service import AIService


def main():

    target_url = "https://example.com"

    # ---------------------------------------------------------
    # 1. SECURITY SCAN
    # ---------------------------------------------------------

    print("[SCAN] Güvenlik taraması başlıyor...")
    print(f"[SCAN] Hedef: {target_url}")

    scanner = SecurityScanner()

    security_result = scanner.scan(target_url)

    print("[SCAN] Güvenlik taraması tamamlandı.")

    # ---------------------------------------------------------
    # 2. SECURITY RESULT -> DICT
    # ---------------------------------------------------------

    security_data = security_result.to_dict()

    # ---------------------------------------------------------
    # 3. AI
    # ---------------------------------------------------------

    ai = AIService()

    report = ai.generate_security_report(
        security_data
    )

    # ---------------------------------------------------------
    # 4. RESULT
    # ---------------------------------------------------------

    print("\n===== GÜVENLİK RAPORU =====\n")
    print(report)


if __name__ == "__main__":
    main()