import json
import os

from openai import OpenAI


class AIService:

    def __init__(self):

        # Foundry Local adresi
        self.base_url = os.getenv(
            "FOUNDRY_BASE_URL",
            "http://127.0.0.1:52511/v1"
        )

        # Kullanacağımız model
        self.model = os.getenv(
            "FOUNDRY_MODEL",
            "qwen3-4b-cuda-gpu"
        )

        # OpenAI uyumlu Foundry Local API client
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="local"
        )

    # ---------------------------------------------------------
    # MODEL İSTEĞİ
    # ---------------------------------------------------------

    def ask(self, prompt: str) -> str:

        print("\n[AI] Model isteği gönderiliyor...")
        print(f"[AI] Model: {self.model}")
        print(f"[AI] Base URL: {self.base_url}")

        # Qwen3 için non-thinking modu.
        #
        # /no_think:
        # Modelden düşünme bölümünü üretmemesini istiyoruz.
        #
        # enable_thinking=False:
        # Qwen3'ün resmi hard-switch yöntemidir.
        user_prompt = f"""
/no_think

{prompt}
"""

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        
                       " /no_think Sen profesyonel bir web güvenlik analiz asistanısın.\n"
                        "Yalnızca sana verilen güvenlik taraması verilerini kullan.\n"
                        "Verilmeyen bir güvenlik açığını varsayma.\n"
                        "Kısa, doğru ve profesyonel Türkçe bir güvenlik raporu üret.\n"
                        "Yanıtında düşünme sürecini gösterme.\n"
                        "Yanıt yalnızca nihai rapor olmalıdır."
                    )
                },
                {
                    "role": "user /no_think",
                    "content": user_prompt
                }
            ],

            # Qwen3 non-thinking için önerilen değerler
            temperature=0.2,
            top_p=0.8,

            # Raporun yarıda kesilmesini önlemek için
            max_tokens=2000,

            # Qwen3 thinking'i kapatmayı OpenAI-compatible
            # API üzerinden de talep ediyoruz.
            extra_body={
                "enable_thinking": False
            }
        )

        print("[AI] Model cevap verdi.")

        # Finish reason
        finish_reason = response.choices[0].finish_reason

        print(f"[AI] Finish reason: {finish_reason}")

        # Modelin döndürdüğü asıl içerik
        content = response.choices[0].message.content
        

        if not content:
         raise RuntimeError("Model boş güvenlik raporu döndürdü.")
        
        print(
            f"[AI] Ham cevap uzunluğu: {len(content)} karakter"
        )

        return content

    # ---------------------------------------------------------
    # GÜVENLİK RAPORU
    # ---------------------------------------------------------

    def generate_security_report(
        self,
        security_result: dict
    ) -> str:

        print("[AI] Güvenlik verisi hazırlanıyor...")
        print("[AI] Güvenlik raporu oluşturuluyor...")

        # Scanner'dan gelen JSON'u düzgün biçimde modele gönderiyoruz.
        security_json = json.dumps(
            security_result,
            ensure_ascii=False,
            indent=2
        )

        user_prompt = f"""
        /no_think
Aşağıdaki JSON, bir web sitesine ait güvenlik taraması sonucudur.

SADECE bu JSON içerisinde bulunan bilgileri kullan.

JSON:

{security_json}

Bu verilere dayanarak kısa ve profesyonel bir Türkçe güvenlik raporu oluştur.

Rapor tam olarak şu bölümlerden oluşsun:

## Yönetici Özeti

En fazla 3 cümle.

## Teknik Bulgular

Önemli güvenlik bulgularını listele.

Her bulgu şu formatta olsun:

### Bulgu: [bulgu adı]
- Durum: Olumlu / Olumsuz
- Risk: Düşük / Orta / Yüksek / Kritik
- Açıklama: [tek kısa cümle]

## Risk Seviyesi

Tek cümle ile genel risk seviyesini belirt.

## Çözüm Önerileri

En fazla 5 maddelik çözüm önerisi ver.

## Sonuç

En fazla 2 cümlelik sonuç yaz.

Kurallar:

1. JSON'da bulunmayan bir açığı varsayma.
2. Aynı bulguyu tekrar etme.
3. Gereksiz teknik açıklama yapma.
4. İngilizce cevap verme.
5. Yalnızca nihai raporu üret.
6. Düşünme sürecini gösterme.
7. <think> etiketi üretme.
8. Raporu gereksiz yere uzatma.
"""

        report = self.ask(user_prompt)

        print("[AI] Güvenlik raporu alındı.")

        return report

    # ---------------------------------------------------------
    # ÖZET
    # ---------------------------------------------------------

    def summarize_report(
        self,
        report: str
    ) -> str:

        prompt = f"""
Aşağıdaki güvenlik raporunu Türkçe olarak çok kısa şekilde özetle.

Raporda olmayan bilgi ekleme.

Rapor:

{report}
"""

        return self.ask(prompt)

    # ---------------------------------------------------------
    # GENEL CHAT
    # ---------------------------------------------------------

    def chat(
        self,
        message: str
    ) -> str:

        return self.ask(message)