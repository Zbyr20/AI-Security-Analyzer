import { buildSummary } from "../lib/summary.js";

const STATUS_LABELS = {
    ok: "İyi",
    warn: "Dikkat",
    bad: "Sorun",
    unknown: "Bilinmiyor",
};

export default function ScanSummary({ scan }) {
    const cards = buildSummary(scan);
    if (cards.length === 0) return null;

    return (
        <ul className="summary">
            {cards.map((card) => (
                <li key={card.key} className={`card card--${card.status}`}>
                    <div className="card__top">
                        <span className="card__title">{card.title}</span>
                        <span className="badge">{STATUS_LABELS[card.status]}</span>
                    </div>
                    <div className="card__headline">{card.headline}</div>
                    {card.details.length > 0 && (
                        <ul className="card__details">
                            {card.details.map((detail, index) => (
                                <li key={index}>{detail}</li>
                            ))}
                        </ul>
                    )}
                </li>
            ))}
        </ul>
    );
}
