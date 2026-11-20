// Ham tarama sonucunu (/scan cevabındaki "scan" alanı) ekranda
// gösterilecek özet kartlarına çevirir.
//
// Her kart: { key, title, status: "ok" | "warn" | "bad" | "unknown",
//             headline, details: [metin, ...] }
//
// TLS ve port kartları yalnızca backend bu alanları gönderiyorsa
// eklenir; böylece eski ve yeni backend sürümleriyle de çalışır.

const HEADER_LABELS = {
    csp: "Content-Security-Policy",
    hsts: "Strict-Transport-Security",
    x_frame_options: "X-Frame-Options",
    x_content_type_options: "X-Content-Type-Options",
    referrer_policy: "Referrer-Policy",
    permissions_policy: "Permissions-Policy",
};

function sslCard(ssl) {
    const card = { key: "ssl", title: "SSL sertifikası", details: [] };
    if (!ssl) return { ...card, status: "unknown", headline: "Veri yok" };

    if (ssl.ssl_valid) {
        card.status = "ok";
        card.headline = "Geçerli";
        const notAfter = ssl.certificate && ssl.certificate.notAfter;
        if (notAfter) card.details.push(`Son geçerlilik: ${notAfter}`);
    } else {
        card.status = "bad";
        card.headline = "Geçersiz veya alınamadı";
        if (ssl.error) card.details.push(ssl.error);
    }
    return card;
}

function headersCard(headers) {
    const card = { key: "headers", title: "Güvenlik başlıkları", details: [] };
    if (!headers) return { ...card, status: "unknown", headline: "Veri yok" };
    if (headers.error) {
        return { ...card, status: "unknown", headline: "Taranamadı", details: [headers.error] };
    }

    const keys = Object.keys(HEADER_LABELS);
    const missing = keys.filter((key) => headers[key] !== true);
    const present = keys.length - missing.length;

    card.headline = `${present}/${keys.length} mevcut`;
    card.status = missing.length === 0 ? "ok" : missing.length <= 2 ? "warn" : "bad";
    if (missing.length) {
        card.details.push(
            "Eksik: " + missing.map((key) => HEADER_LABELS[key]).join(", ")
        );
    }
    return card;
}

function cookiesCard(cookies) {
    const card = { key: "cookies", title: "Çerezler", details: [] };
    if (!cookies) return { ...card, status: "unknown", headline: "Veri yok" };
    if (cookies.error) {
        return { ...card, status: "unknown", headline: "Taranamadı", details: [cookies.error] };
    }

    const list = Array.isArray(cookies.cookies) ? cookies.cookies : [];
    if (list.length === 0) {
        return { ...card, status: "ok", headline: "Çerez yok" };
    }

    const weak = list.filter((c) => !c.secure || !c.httponly);
    card.headline = `${list.length} çerez`;
    card.status = weak.length === 0 ? "ok" : "warn";
    for (const c of weak) {
        const flags = [];
        if (!c.secure) flags.push("Secure");
        if (!c.httponly) flags.push("HttpOnly");
        card.details.push(`${c.name}: ${flags.join(" ve ")} eksik`);
    }
    return card;
}

function dnsCard(dns) {
    const card = { key: "dns", title: "DNS", details: [] };
    if (!dns || Object.keys(dns).length === 0) {
        return { ...card, status: "unknown", headline: "Veri yok" };
    }

    const a = dns.a || [];
    const aaaa = dns.aaaa || [];
    // DNS bilgilendirme amaçlıdır; eksik kayıt tek başına açık değildir.
    card.status = dns.error ? "unknown" : "ok";
    card.headline = `${a.length} IPv4, ${aaaa.length} IPv6`;
    if (a.length) card.details.push(`A: ${a.join(", ")}`);
    if ((dns.mx || []).length) card.details.push(`MX: ${dns.mx.join(", ")}`);
    if (dns.error) card.details.push(dns.error);
    return card;
}

function tlsCard(tls) {
    const card = { key: "tls", title: "TLS protokolleri", details: [] };
    if (tls.error) {
        return { ...card, status: "unknown", headline: "Taranamadı", details: [tls.error] };
    }
    const weak = tls.weak_protocols || [];
    card.headline = tls.highest_protocol
        ? `En yüksek: ${tls.highest_protocol}`
        : "Protokol bulunamadı";
    card.status = weak.length ? "bad" : tls.supports_tls13 ? "ok" : "warn";
    if (weak.length) card.details.push(`Zayıf: ${weak.join(", ")}`);
    if (!tls.supports_tls13) card.details.push("TLS 1.3 desteklenmiyor");
    return card;
}

function portsCard(ports) {
    const card = { key: "ports", title: "Açık portlar", details: [] };
    if (ports.error) {
        return { ...card, status: "unknown", headline: "Taranamadı", details: [ports.error] };
    }
    const open = ports.open_ports || [];
    const risky = ports.risky_open_ports || [];
    card.headline = `${open.length} açık`;
    card.status = risky.length ? "bad" : "ok";
    for (const p of risky) {
        card.details.push(`${p.port} (${p.service}): ${p.reason}`);
    }
    return card;
}

export function buildSummary(scan) {
    if (!scan || typeof scan !== "object") return [];

    const cards = [
        sslCard(scan.ssl),
        headersCard(scan.headers),
        cookiesCard(scan.cookies),
        dnsCard(scan.dns),
    ];
    if (scan.tls) cards.push(tlsCard(scan.tls));
    if (scan.ports) cards.push(portsCard(scan.ports));
    return cards;
}
