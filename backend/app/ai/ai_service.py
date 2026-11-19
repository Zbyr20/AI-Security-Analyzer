import json
import re

from openai import OpenAI

from app.config import (
    FOUNDRY_BASE_URL,
    MODEL_NAME,
    API_KEY,
)


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def clean_model_output(content: str) -> str:
    """Model cevabındaki <think> bölümlerini ve satır sonu farklarını temizler.

    - Kapalı <think>...</think> blokları silinir (birden fazla olabilir).
    - Sadece </think> varsa (açılış etiketi atlanmışsa) öncesi silinir.
    - Sadece <think> varsa (cevap yarıda kesilmişse) sonrası silinir.
    - Windows (\\r\\n) ve eski Mac (\\r) satır sonları \\n yapılır,
      satır sonundaki boşluklar silinir.
    """
    content = str(content)
    content = _THINK_BLOCK.sub("", content)

    lower = content.lower()
    end = lower.find("</think>")
    if end != -1:
        content = content[end + len("</think>"):]
        lower = content.lower()

    start = lower.find("<think>")
    if start != -1:
        content = content[:start]

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    content = "\n".join(line.rstrip() for line in content.split("\n"))
    return content.strip()


class AIService:

    def __init__(self, client=None):

        self.base_url = FOUNDRY_BASE_URL
        self.model = MODEL_NAME

        # Testlerde sahte istemci verilebilir; normalde gerçek OpenAI istemcisi.
        self.client = client or OpenAI(
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
        user_prompt = f"/no_think\n{prompt}"

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

                temperature=0.1,
                top_p=0.7,

                # Kısa ama yeterli rapor alanı
                max_tokens=800,
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

        content = clean_model_output(content)

        if not content:

            raise RuntimeError(
                "Model yalnızca düşünme çıktısı döndürdü, rapor boş."
            )

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

ÖNEMLİ KURALLAR:
- Düşünme sürecini yazma.
- Sadece nihai rapor çıktısını ver.
- <think> ... </think> bloklarını çıkar.
- Yalnızca markdown formatında yaz.
- Her başlık ve madde ayrı satırda olsun.
- Tek bir paragraf halinde yazma.
- Tek bir satırda uzun metin üretme.

Şu yapıyı kullan:

## Yönetici Özeti

Kısa özet.

## Teknik Bulgular

### Bulgu: [isim]

- Durum: Olumlu veya Olumsuz
- Risk: Düşük, Orta, Yüksek veya Kritik
- Açıklama: Tek kısa cümle

## Risk Seviyesi

Genel risk seviyesi ve tek cümle gerekçe.

## Çözüm Önerileri

- Öneri 1
- Öneri 2

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

        try:
            report = self.ask(user_prompt)
            print(
                "[AI] Güvenlik raporu alındı."
            )
            return report
        except Exception as exc:
            print(
                "[AI] Model erişilemedi; otomatik yedek rapor dönülüyor. "
                f"Hata: {exc}"
            )
            return (
                "AI modeli şu an erişilemediği için otomatik yedek rapor üretildi.\n\n"
                "Tarama verileri başarıyla toplandı.\n"
                "Lütfen model hizmeti erişilebilir olduğunda raporu yeniden oluşturun.\n\n"
                f"Tarama sonucu:\n{security_json}"
            )

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