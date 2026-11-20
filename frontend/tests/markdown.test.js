import { test } from "node:test";
import assert from "node:assert/strict";

import { parseMarkdown, parseInline } from "../src/lib/markdown.js";

test("AI rapor şablonu başlık, liste ve paragraflara ayrılır", () => {
    const report = [
        "## Yönetici Özeti",
        "",
        "Site genel olarak güvenli.",
        "",
        "## Teknik Bulgular",
        "",
        "### Bulgu: HSTS eksik",
        "",
        "- Durum: Olumsuz",
        "- Risk: Orta",
        "",
        "1. Birinci öneri",
        "2. İkinci öneri",
    ].join("\n");

    assert.deepEqual(parseMarkdown(report), [
        { type: "heading", level: 2, text: "Yönetici Özeti" },
        { type: "paragraph", lines: ["Site genel olarak güvenli."] },
        { type: "heading", level: 2, text: "Teknik Bulgular" },
        { type: "heading", level: 3, text: "Bulgu: HSTS eksik" },
        { type: "list", ordered: false, items: ["Durum: Olumsuz", "Risk: Orta"] },
        { type: "list", ordered: true, items: ["Birinci öneri", "İkinci öneri"] },
    ]);
});

test("Windows satır sonları (CRLF) sorun çıkarmaz", () => {
    assert.deepEqual(parseMarkdown("## Başlık\r\n\r\nMetin\r\n"), [
        { type: "heading", level: 2, text: "Başlık" },
        { type: "paragraph", lines: ["Metin"] },
    ]);
});

test("ardışık satırlar tek paragrafta satır satır korunur (yedek rapor JSON'u)", () => {
    const blocks = parseMarkdown('Tarama sonucu:\n{\n  "url": "https://a.com"\n}');
    assert.equal(blocks.length, 1);
    assert.deepEqual(blocks[0].lines, ["Tarama sonucu:", "{", '  "url": "https://a.com"', "}"]);
});

test("kod bloğu içeriği ayrıştırılmadan alınır", () => {
    assert.deepEqual(parseMarkdown("```json\n## değil başlık\n- değil madde\n```"), [
        { type: "code", text: "## değil başlık\n- değil madde" },
    ]);
});

test("kapanmamış kod bloğu metnin sonuna kadar sürer", () => {
    assert.deepEqual(parseMarkdown("```\nx = 1"), [{ type: "code", text: "x = 1" }]);
});

test("yatay çizgi ve * ile madde işaretleri", () => {
    assert.deepEqual(parseMarkdown("---\n* a\n* b"), [
        { type: "hr" },
        { type: "list", ordered: false, items: ["a", "b"] },
    ]);
});

test("başlık sonundaki # işaretleri atılır", () => {
    assert.deepEqual(parseMarkdown("# Sonuç ##"), [{ type: "heading", level: 1, text: "Sonuç" }]);
});

test("boş veya null girdi boş liste döner", () => {
    assert.deepEqual(parseMarkdown(""), []);
    assert.deepEqual(parseMarkdown(null), []);
});

test("satır içi kalın ve kod ayrıştırılır", () => {
    assert.deepEqual(parseInline("Risk: **Yüksek** — `Strict-Transport-Security` eksik"), [
        { type: "text", text: "Risk: " },
        { type: "strong", text: "Yüksek" },
        { type: "text", text: " — " },
        { type: "code", text: "Strict-Transport-Security" },
        { type: "text", text: " eksik" },
    ]);
});

test("HTML etiketleri düz metin olarak kalır (enjeksiyon yok)", () => {
    const parts = parseInline('<img src=x onerror="alert(1)">');
    assert.deepEqual(parts, [{ type: "text", text: '<img src=x onerror="alert(1)">' }]);
});
