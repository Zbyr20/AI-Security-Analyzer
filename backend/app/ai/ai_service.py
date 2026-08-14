import json

from openai import OpenAI

from app.config import (
    FOUNDRY_BASE_URL,
    MODEL_NAME,
    API_KEY,
)


class AIService:

    def __init__(self):

        self.base_url = FOUNDRY_BASE_URL
        self.model = MODEL_NAME

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=API_KEY,
        )

    # ---------------------------------------------------------
    # MODEL İSTEĞİ
    # ---------------------------------------------------------

    def ask(self, prompt: str) -> str:

        print()
        print("[AI] Model isteği gönderiliyor...")
        print(f"[AI] Model: {self.model}")
        print(f"[AI] Base URL: {self.base_url}")

        # Qwen3 non-thinking modu.
        # Bunu doğrudan prompt içinde kullanıyoruz çünkü
        # Foundry üzerinden yaptığımız testte /no_think çalıştı.
        user_prompt = f"/no_think\n\n{prompt}"

        try:

            response = self.client.chat.completions.create(
                model=self.model,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen profesyonel bir web güvenlik "
                            "raporlama asistanısın.\n"
                            "Yalnızca verilen güvenlik taraması "
                            "verilerini kullan.\n"
                            "Verilmeyen güvenlik açıklarını varsayma.\n"
                            "Yalnızca nihai cevabı üret.\n"
                            "Türkçe yaz."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],

                temperature=0.2,
                top_p=0.8,

                # Kısa ama yeterli rapor alanı
                max_tokens=1200,
            )

        except Exception as exc:

            raise RuntimeError(
                f"AI modeline bağlanırken hata oluştu: {exc}"
            ) from exc

        print("[AI] Model cevap verdi.")

        if not response.choices:

            raise RuntimeError(
                "Model herhangi bir cevap döndürmedi."
            )

        choice = response.choices[0]

        print(
            f"[AI] Finish reason: "
            f"{choice.finish_reason}"
        )

        content = choice.message.content

        if not content:

            raise RuntimeError(
                "Model boş cevap döndürdü."
            )

        content = content.strip()

        print(
            f"[AI] Ham cevap uzunluğu: "
            f"{len(content)} karakter"
        )

        return content

    # ---------------------------------------------------------
    # GÜVENLİK RAPORU
    # ---------------------------------------------------------

    def generate_security_report(
        self,
        security_result: dict,
    ) -> str:

        print(
            "[AI] Güvenlik verisi hazırlanıyor..."
        )

        security_json = json.dumps(
            security_result,
            ensure_ascii=False,
            indent=2,
        )

        print(
            "[AI] Güvenlik raporu oluşturuluyor..."
        )

        user_prompt = f"""
Aşağıdaki JSON bir web sitesinin güvenlik taraması sonucudur.

SADECE bu JSON içerisindeki bilgileri kullan.

JSON:
{security_json}

Verilere dayanarak kısa ve profesyonel bir Türkçe
güvenlik raporu oluştur.

Şu yapıyı kullan:

## Yönetici Özeti

Kısa özet.

## Teknik Bulgular

Yalnızca JSON'da bulunan önemli bulgular.

Her bulgu:

### Bulgu: [isim]

- Durum: Olumlu veya Olumsuz
- Risk: Düşük, Orta, Yüksek veya Kritik
- Açıklama: Tek kısa cümle

## Risk Seviyesi

Genel risk seviyesi ve tek cümle gerekçe.

## Çözüm Önerileri

Yalnızca JSON'daki olumsuz bulgulara yönelik öneriler.

## Sonuç

Kısa sonuç.

Kurallar:

- JSON'da olmayan açık üretme.
- SQL Injection, XSS, IDOR vb. bilgiler JSON'da yoksa bunlardan bahsetme.
- DNS kaydının boş olmasını tek başına güvenlik açığı kabul etme.
- Aynı bulguyu tekrar etme.
- Gerçek olmayan tarih, domain, CVE, port veya sayı üretme.
- Tarama yapılmamış bir sistemi taranmış gibi gösterme.
- Yalnızca mevcut verileri yorumla.
- Gereksiz açıklama yapma.
"""

        report = self.ask(user_prompt)

        print(
            "[AI] Güvenlik raporu alındı."
        )

        return report

    # ---------------------------------------------------------
    # RAPOR ÖZETLEME
    # ---------------------------------------------------------

    def summarize_report(
        self,
        report: str,
    ) -> str:

        prompt = f"""
Aşağıdaki güvenlik raporunu kısa Türkçe özetle.

Yalnızca raporda bulunan bilgileri kullan.

Rapor:

{report}
"""

        return self.ask(prompt)

    # ---------------------------------------------------------
    # GENEL CHAT
    # ---------------------------------------------------------

    def chat(
        self,
        message: str,
    ) -> str:

        return self.ask(message)