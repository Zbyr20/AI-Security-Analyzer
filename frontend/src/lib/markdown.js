// AI raporundaki markdown'ı basit bir blok listesine çevirir.
//
// Neden kütüphane yok? Rapor yalnızca başlık, madde, kalın yazı ve
// kod kullanıyor. Kendi küçük ayrıştırıcımız HTML üretmez; React
// elemanlarına çevrildiği için modelden gelen metin sayfaya HTML
// olarak enjekte edilemez (XSS riski yok).
//
// Blok türleri:
//   { type: "heading", level: 1-6, text }
//   { type: "list", ordered: bool, items: [text, ...] }
//   { type: "code", text }
//   { type: "hr" }
//   { type: "paragraph", lines: [text, ...] }

const HEADING = /^(#{1,6})\s+(.*?)\s*#*\s*$/;
const UNORDERED = /^\s*[-*+]\s+(.*)$/;
const ORDERED = /^\s*\d+[.)]\s+(.*)$/;
const FENCE = /^\s*```/;
const HR = /^\s*([-*_])(\s*\1){2,}\s*$/;

export function parseMarkdown(source) {
    const lines = String(source ?? "").replace(/\r\n?/g, "\n").split("\n");
    const blocks = [];
    let paragraph = null;
    let list = null;

    const closeParagraph = () => {
        if (paragraph) blocks.push(paragraph);
        paragraph = null;
    };
    const closeList = () => {
        if (list) blocks.push(list);
        list = null;
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        if (FENCE.test(line)) {
            closeParagraph();
            closeList();
            const code = [];
            i++;
            while (i < lines.length && !FENCE.test(lines[i])) {
                code.push(lines[i]);
                i++;
            }
            blocks.push({ type: "code", text: code.join("\n") });
            continue;
        }

        if (!line.trim()) {
            closeParagraph();
            closeList();
            continue;
        }

        if (HR.test(line)) {
            closeParagraph();
            closeList();
            blocks.push({ type: "hr" });
            continue;
        }

        const heading = line.match(HEADING);
        if (heading) {
            closeParagraph();
            closeList();
            blocks.push({
                type: "heading",
                level: heading[1].length,
                text: heading[2],
            });
            continue;
        }

        const unordered = line.match(UNORDERED);
        const ordered = unordered ? null : line.match(ORDERED);
        if (unordered || ordered) {
            closeParagraph();
            const isOrdered = Boolean(ordered);
            if (list && list.ordered !== isOrdered) closeList();
            if (!list) list = { type: "list", ordered: isOrdered, items: [] };
            list.items.push((unordered || ordered)[1]);
            continue;
        }

        closeList();
        if (!paragraph) paragraph = { type: "paragraph", lines: [] };
        paragraph.lines.push(line);
    }

    closeParagraph();
    closeList();
    return blocks;
}

// Satır içi biçim: **kalın**, __kalın__ ve `kod`.
// Sonuç: [{ type: "text" | "strong" | "code", text }]
const INLINE = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__)/g;

export function parseInline(text) {
    const parts = [];
    let last = 0;
    const source = String(text ?? "");

    for (const match of source.matchAll(INLINE)) {
        if (match.index > last) {
            parts.push({ type: "text", text: source.slice(last, match.index) });
        }
        const token = match[0];
        if (token.startsWith("`")) {
            parts.push({ type: "code", text: token.slice(1, -1) });
        } else {
            parts.push({ type: "strong", text: token.slice(2, -2) });
        }
        last = match.index + token.length;
    }

    if (last < source.length) {
        parts.push({ type: "text", text: source.slice(last) });
    }
    return parts;
}
