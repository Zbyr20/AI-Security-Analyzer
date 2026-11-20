import { parseMarkdown, parseInline } from "../lib/markdown.js";

// Markdown metnini React elemanlarına çevirir.
// dangerouslySetInnerHTML kullanılmaz: modelin ürettiği metin
// her zaman düz metin olarak gösterilir.

function Inline({ text }) {
    return parseInline(text).map((part, index) => {
        if (part.type === "strong") return <strong key={index}>{part.text}</strong>;
        if (part.type === "code") return <code key={index}>{part.text}</code>;
        return <span key={index}>{part.text}</span>;
    });
}

function Block({ block }) {
    switch (block.type) {
        case "heading": {
            // Sayfanın h1'i başlıkta; rapor başlıkları h2'den başlar.
            const level = Math.min(block.level + 1, 6);
            const Tag = `h${level}`;
            return (
                <Tag>
                    <Inline text={block.text} />
                </Tag>
            );
        }
        case "list": {
            const Tag = block.ordered ? "ol" : "ul";
            return (
                <Tag>
                    {block.items.map((item, index) => (
                        <li key={index}>
                            <Inline text={item} />
                        </li>
                    ))}
                </Tag>
            );
        }
        case "code":
            return (
                <pre>
                    <code>{block.text}</code>
                </pre>
            );
        case "hr":
            return <hr />;
        default:
            return (
                <p>
                    {block.lines.map((line, index) => (
                        <span key={index}>
                            {index > 0 && <br />}
                            <Inline text={line} />
                        </span>
                    ))}
                </p>
            );
    }
}

export default function Markdown({ source }) {
    return (
        <div className="markdown">
            {parseMarkdown(source).map((block, index) => (
                <Block key={index} block={block} />
            ))}
        </div>
    );
}
