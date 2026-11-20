// Backend ile konuşan tek yer. React'ten bağımsız olduğu için
// `node --test` ile tarayıcı açmadan test edilebilir.

// Vite, VITE_ ile başlayan ortam değişkenlerini derlemeye gömer.
// Örnek (PowerShell): $env:VITE_API_URL = "http://localhost:9000"; npm run dev
export const DEFAULT_API_URL =
    (typeof import.meta !== "undefined" &&
        import.meta.env &&
        import.meta.env.VITE_API_URL) ||
    "http://127.0.0.1:8000";

// FastAPI hata gövdesinden okunabilir bir mesaj çıkarır.
// - HTTPException: {"detail": "metin"}
// - Pydantic doğrulama (422): {"detail": [{"loc": [...], "msg": "..."}]}
export function extractErrorMessage(body, status) {
    const detail = body && body.detail;

    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
        return detail
            .map((item) => (item && item.msg) || String(item))
            .join("; ");
    }

    if (status === 400) return "Geçersiz istek.";
    if (status >= 500) return "Sunucu hatası oluştu.";
    return `İstek başarısız oldu (HTTP ${status}).`;
}

export async function scanWebsite(url, options = {}) {
    const fetchImpl = options.fetchImpl || globalThis.fetch;
    const baseUrl = (options.baseUrl || DEFAULT_API_URL).replace(/\/+$/, "");
    const trimmed = (url || "").trim();

    if (!trimmed) {
        throw new Error("Lütfen bir URL girin.");
    }

    let response;
    try {
        response = await fetchImpl(`${baseUrl}/scan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: trimmed }),
        });
    } catch {
        // fetch yalnızca ağ hatasında (sunucu kapalı, CORS) fırlatır.
        throw new Error(
            `Backend'e ulaşılamadı (${baseUrl}). Sunucu çalışıyor mu?`
        );
    }

    // Gövde JSON değilse (örn. proxy'nin HTML hata sayfası) null kabul et.
    const body = await response.json().catch(() => null);

    if (!response.ok) {
        throw new Error(extractErrorMessage(body, response.status));
    }

    if (!body || typeof body !== "object") {
        throw new Error("Sunucudan beklenmeyen bir cevap geldi.");
    }

    return body;
}
