import { test } from "node:test";
import assert from "node:assert/strict";

import { buildSummary } from "../src/lib/summary.js";

const ALL_HEADERS = {
    error: null,
    csp: true,
    hsts: true,
    x_frame_options: true,
    x_content_type_options: true,
    referrer_policy: true,
    permissions_policy: true,
};

const byKey = (cards) => Object.fromEntries(cards.map((c) => [c.key, c]));

test("sağlıklı site için temel dört kart 'ok' olur", () => {
    const cards = buildSummary({
        ssl: { ssl_valid: true, certificate: { notAfter: "Jan  1 00:00:00 2027 GMT" } },
        headers: ALL_HEADERS,
        cookies: { cookies_found: false, cookies: [], error: null },
        dns: { domain: "a.com", a: ["1.2.3.4"], aaaa: [], mx: [], ns: [], cname: [], error: null },
    });
    assert.deepEqual(cards.map((c) => c.key), ["ssl", "headers", "cookies", "dns"]);
    assert.ok(cards.every((c) => c.status === "ok"));
    assert.deepEqual(byKey(cards).ssl.details, ["Son geçerlilik: Jan  1 00:00:00 2027 GMT"]);
    assert.equal(byKey(cards).headers.headline, "6/6 mevcut");
});

test("geçersiz SSL 'bad' ve hata mesajı detayda", () => {
    const { ssl } = byKey(buildSummary({ ssl: { ssl_valid: false, certificate: null, error: "certificate has expired" } }));
    assert.equal(ssl.status, "bad");
    assert.deepEqual(ssl.details, ["certificate has expired"]);
});

test("eksik başlık sayısına göre warn/bad ve eksikler listelenir", () => {
    const twoMissing = { ...ALL_HEADERS, csp: false, hsts: false };
    const h1 = byKey(buildSummary({ headers: twoMissing })).headers;
    assert.equal(h1.status, "warn");
    assert.equal(h1.headline, "4/6 mevcut");
    assert.deepEqual(h1.details, ["Eksik: Content-Security-Policy, Strict-Transport-Security"]);

    const threeMissing = { ...twoMissing, referrer_policy: false };
    assert.equal(byKey(buildSummary({ headers: threeMissing })).headers.status, "bad");
});

test("başlıklar taranamadıysa 'unknown'", () => {
    const h = byKey(buildSummary({ headers: { error: "Headerlar taranamadı!!" } })).headers;
    assert.equal(h.status, "unknown");
    assert.equal(h.headline, "Taranamadı");
});

test("Secure/HttpOnly eksik çerezler uyarı verir", () => {
    const { cookies } = byKey(buildSummary({
        cookies: {
            cookies_found: true,
            error: null,
            cookies: [
                { name: "sid", secure: true, httponly: true },
                { name: "pref", secure: false, httponly: true },
                { name: "track", secure: false, httponly: false },
            ],
        },
    }));
    assert.equal(cookies.status, "warn");
    assert.equal(cookies.headline, "3 çerez");
    assert.deepEqual(cookies.details, ["pref: Secure eksik", "track: Secure ve HttpOnly eksik"]);
});

test("boş DNS tek başına sorun sayılmaz", () => {
    const { dns } = byKey(buildSummary({ dns: { domain: "a.com", a: [], aaaa: [], mx: [], error: null } }));
    assert.equal(dns.status, "ok");
    assert.equal(dns.headline, "0 IPv4, 0 IPv6");
});

test("eksik alanlar 'Veri yok' olarak gösterilir", () => {
    const cards = buildSummary({});
    assert.equal(cards.length, 4);
    assert.ok(cards.every((c) => c.status === "unknown" && c.headline === "Veri yok"));
});

test("TLS ve port alanları yoksa kartları da yok (eski backend)", () => {
    const keys = buildSummary({ ssl: { ssl_valid: true } }).map((c) => c.key);
    assert.ok(!keys.includes("tls") && !keys.includes("ports"));
});

test("zayıf TLS protokolü 'bad'", () => {
    const { tls } = byKey(buildSummary({
        tls: { highest_protocol: "TLSv1.2", weak_protocols: ["TLSv1.0"], supports_tls13: false, error: null },
    }));
    assert.equal(tls.status, "bad");
    assert.equal(tls.headline, "En yüksek: TLSv1.2");
    assert.deepEqual(tls.details, ["Zayıf: TLSv1.0", "TLS 1.3 desteklenmiyor"]);
});

test("TLS 1.3 varsa ve zayıf yoksa 'ok'", () => {
    const { tls } = byKey(buildSummary({
        tls: { highest_protocol: "TLSv1.3", weak_protocols: [], supports_tls13: true, error: null },
    }));
    assert.equal(tls.status, "ok");
    assert.deepEqual(tls.details, []);
});

test("riskli açık port 'bad' ve gerekçesiyle listelenir", () => {
    const { ports } = byKey(buildSummary({
        ports: {
            open_ports: [{ port: 443, service: "HTTPS" }, { port: 6379, service: "Redis" }],
            risky_open_ports: [{ port: 6379, service: "Redis", reason: "Redis varsayılan olarak kimlik doğrulamasız çalışır." }],
            error: null,
        },
    }));
    assert.equal(ports.status, "bad");
    assert.equal(ports.headline, "2 açık");
    assert.deepEqual(ports.details, ["6379 (Redis): Redis varsayılan olarak kimlik doğrulamasız çalışır."]);
});

test("geçersiz girdi boş liste döner", () => {
    assert.deepEqual(buildSummary(null), []);
    assert.deepEqual(buildSummary("x"), []);
});
