// Çalıştırma: npm test   (Node'un yerleşik test koşucusu, ek paket yok)
import { test } from "node:test";
import assert from "node:assert/strict";

import { scanWebsite, extractErrorMessage } from "../src/lib/api.js";

// Gerçek ağa çıkmadan fetch'i taklit eden yardımcı.
function fakeFetch({ status = 200, body, throws = false, invalidJson = false } = {}) {
    const calls = [];
    const impl = async (url, init) => {
        calls.push({ url, init });
        if (throws) throw new TypeError("Failed to fetch");
        return {
            ok: status >= 200 && status < 300,
            status,
            json: async () => {
                if (invalidJson) throw new SyntaxError("Unexpected token");
                return body;
            },
        };
    };
    return { impl, calls };
}

test("başarılı taramada cevap gövdesi döner ve istek doğru kurulur", async () => {
    const body = { url: "https://example.com", scan: {}, report: "## Rapor" };
    const { impl, calls } = fakeFetch({ body });

    const result = await scanWebsite("  https://example.com  ", {
        fetchImpl: impl,
        baseUrl: "http://api.test/",
    });

    assert.deepEqual(result, body);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "http://api.test/scan");
    assert.equal(calls[0].init.method, "POST");
    assert.deepEqual(JSON.parse(calls[0].init.body), { url: "https://example.com" });
});

test("400 cevabında backend'in detail mesajı gösterilir", async () => {
    const { impl } = fakeFetch({ status: 400, body: { detail: "URL http veya https ile başlamalı." } });
    await assert.rejects(
        scanWebsite("ftp://x", { fetchImpl: impl }),
        { message: "URL http veya https ile başlamalı." }
    );
});

test("500 cevabında detail mesajı gösterilir", async () => {
    const { impl } = fakeFetch({ status: 500, body: { detail: "Model zaman aşımı" } });
    await assert.rejects(scanWebsite("https://a.com", { fetchImpl: impl }), {
        message: "Model zaman aşımı",
    });
});

test("JSON olmayan hata gövdesinde genel mesaj kullanılır", async () => {
    const { impl } = fakeFetch({ status: 502, invalidJson: true });
    await assert.rejects(scanWebsite("https://a.com", { fetchImpl: impl }), {
        message: "Sunucu hatası oluştu.",
    });
});

test("ağ hatasında backend'e ulaşılamadığı söylenir", async () => {
    const { impl } = fakeFetch({ throws: true });
    await assert.rejects(
        scanWebsite("https://a.com", { fetchImpl: impl, baseUrl: "http://api.test" }),
        /Backend'e ulaşılamadı \(http:\/\/api\.test\)/
    );
});

test("boş URL'de istek gönderilmez", async () => {
    const { impl, calls } = fakeFetch({ body: {} });
    await assert.rejects(scanWebsite("   ", { fetchImpl: impl }), {
        message: "Lütfen bir URL girin.",
    });
    assert.equal(calls.length, 0);
});

test("başarılı ama JSON olmayan cevap hata sayılır", async () => {
    const { impl } = fakeFetch({ invalidJson: true });
    await assert.rejects(scanWebsite("https://a.com", { fetchImpl: impl }), {
        message: "Sunucudan beklenmeyen bir cevap geldi.",
    });
});

test("Pydantic 422 hata listesi tek satıra çevrilir", () => {
    const body = { detail: [{ loc: ["body", "url"], msg: "Field required" }, { msg: "ikinci" }] };
    assert.equal(extractErrorMessage(body, 422), "Field required; ikinci");
});

test("detail yoksa durum koduna göre mesaj üretilir", () => {
    assert.equal(extractErrorMessage(null, 400), "Geçersiz istek.");
    assert.equal(extractErrorMessage({}, 404), "İstek başarısız oldu (HTTP 404).");
    assert.equal(extractErrorMessage({ detail: "  " }, 503), "Sunucu hatası oluştu.");
});
