"""AIService testleri. Gerçek modele bağlanılmaz; sahte istemci kullanılır."""
import importlib
from types import SimpleNamespace

import pytest

from app.ai.ai_service import AIService, clean_model_output


# ---------------------------------------------------------
# Sahte OpenAI istemcisi
# ---------------------------------------------------------

def _response(content, finish_reason="stop"):
    message = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=finish_reason)])


class FakeCompletions:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeClient:
    def __init__(self, result):
        self.completions = FakeCompletions(result)
        self.chat = SimpleNamespace(completions=self.completions)


def service_with(result):
    client = FakeClient(result)
    return AIService(client=client), client.completions


# ---------------------------------------------------------
# clean_model_output
# ---------------------------------------------------------

def test_temiz_metin_degismez():
    assert clean_model_output("## Rapor\n\n- madde") == "## Rapor\n\n- madde"


def test_kapali_think_blogu_silinir():
    assert clean_model_output("<think>plan</think>\n## Rapor") == "## Rapor"


def test_think_buyuk_harf_ve_cok_satir():
    assert clean_model_output("<THINK>\na\nb\n</THINK>Sonuç") == "Sonuç"


def test_birden_fazla_think_blogu():
    out = clean_model_output("<think>1</think>A<think>2</think>B")
    assert out == "AB"


def test_acilis_etiketi_yoksa_kapanis_oncesi_silinir():
    # Qwen bazen <think> açılışını yazmadan doğrudan düşünür.
    assert clean_model_output("düşünce...\n</think>\n## Rapor") == "## Rapor"


def test_yarim_kalan_think_silinir():
    assert clean_model_output("## Rapor\n<think>kesildi") == "## Rapor"


def test_gercek_crlf_satir_sonlari_normallesir():
    assert clean_model_output("a\r\nb\rc") == "a\nb\nc"


def test_satir_sonu_bosluklari_silinir():
    assert clean_model_output("a   \nb\t") == "a\nb"


def test_sadece_think_varsa_bos_doner():
    assert clean_model_output("<think>sadece düşünce</think>") == ""


# ---------------------------------------------------------
# AIService.ask
# ---------------------------------------------------------

def test_ask_temizlenmis_cevap_doner():
    service, completions = service_with(_response("<think>x</think>\n## Rapor"))
    assert service.ask("merhaba") == "## Rapor"


def test_ask_no_think_ve_model_gonderir():
    service, completions = service_with(_response("ok"))
    service.ask("soru")
    call = completions.calls[0]
    assert call["model"] == service.model
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["content"] == "/no_think\nsoru"


def test_ask_baglanti_hatasi_runtimeerror():
    service, _ = service_with(ConnectionError("kapalı"))
    with pytest.raises(RuntimeError, match="bağlanırken"):
        service.ask("x")


def test_ask_bos_choices_hata():
    service, _ = service_with(SimpleNamespace(choices=[]))
    with pytest.raises(RuntimeError, match="herhangi bir cevap"):
        service.ask("x")


def test_ask_bos_icerik_hata():
    service, _ = service_with(_response(None))
    with pytest.raises(RuntimeError, match="boş cevap"):
        service.ask("x")


def test_ask_sadece_dusunce_hata():
    service, _ = service_with(_response("<think>uzun düşünce</think>"))
    with pytest.raises(RuntimeError, match="düşünme"):
        service.ask("x")


# ---------------------------------------------------------
# generate_security_report
# ---------------------------------------------------------

def test_rapor_json_prompta_eklenir():
    service, completions = service_with(_response("## Yönetici Özeti"))
    report = service.generate_security_report({"url": "https://örnek.com", "ssl": {"ssl_valid": True}})
    assert report == "## Yönetici Özeti"
    prompt = completions.calls[0]["messages"][1]["content"]
    # ensure_ascii=False: Türkçe karakterler bozulmadan modele gider.
    assert '"url": "https://örnek.com"' in prompt


def test_model_kapaliysa_yedek_rapor():
    service, _ = service_with(ConnectionError("kapalı"))
    report = service.generate_security_report({"url": "https://example.com"})
    assert "yedek rapor" in report
    assert "https://example.com" in report


def test_sadece_dusunce_donerse_yedek_rapor():
    service, _ = service_with(_response("<think>...</think>"))
    report = service.generate_security_report({"url": "https://example.com"})
    assert "yedek rapor" in report


# ---------------------------------------------------------
# config: ortam değişkenleri
# ---------------------------------------------------------

def test_config_varsayilanlar(monkeypatch):
    for name in ("AI_BASE_URL", "AI_MODEL", "AI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    import app.config as config
    config = importlib.reload(config)
    assert config.FOUNDRY_BASE_URL == "http://127.0.0.1:56661/v1"
    assert config.MODEL_NAME == "qwen3-4b-cuda-gpu"
    assert config.API_KEY == "local"


def test_config_ortam_degiskenleri(monkeypatch):
    monkeypatch.setenv("AI_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("AI_MODEL", "qwen3-8b")
    monkeypatch.setenv("AI_API_KEY", "gizli")
    import app.config as config
    config = importlib.reload(config)
    try:
        assert config.FOUNDRY_BASE_URL == "http://localhost:1234/v1"
        assert config.MODEL_NAME == "qwen3-8b"
        assert config.API_KEY == "gizli"
    finally:
        monkeypatch.undo()
        importlib.reload(config)
