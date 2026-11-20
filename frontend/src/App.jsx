import { useState } from "react";

import "./App.css";
import Markdown from "./components/Markdown.jsx";
import ScanSummary from "./components/ScanSummary.jsx";
import { scanWebsite } from "./lib/api.js";

function App() {
    // Kullanıcının girdiği URL
    const [url, setUrl] = useState("");

    // FastAPI'den dönen sonuç: { url, scan, report }
    const [result, setResult] = useState(null);

    // Kullanıcıya gösterilecek hata mesajı
    const [error, setError] = useState("");

    // Tarama devam ediyor mu?
    const [loading, setLoading] = useState(false);

    // <form> kullandığımız için Enter tuşu da taramayı başlatır.
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (loading) return;

        setResult(null);
        setError("");
        setLoading(true);

        try {
            setResult(await scanWebsite(url));
        } catch (err) {
            console.error(err);
            // Backend'in "detail" mesajı (örn. geçersiz URL) burada görünür.
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="app">
            <h1>AI Security Analyzer</h1>

            <form className="scan-form" onSubmit={handleSubmit}>
                <label htmlFor="url" className="visually-hidden">
                    Taranacak URL
                </label>
                <input
                    id="url"
                    type="text"
                    inputMode="url"
                    autoComplete="url"
                    value={url}
                    onChange={(event) => setUrl(event.target.value)}
                    placeholder="https://example.com"
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !url.trim()}>
                    {loading ? "Tarama yapılıyor..." : "Tara"}
                </button>
            </form>

            {loading && (
                <p className="status" role="status">
                    Site taranıyor ve AI raporu hazırlanıyor. Bu biraz sürebilir.
                </p>
            )}

            {error && (
                <p className="error" role="alert">
                    {error}
                </p>
            )}

            {result && (
                <section className="result">
                    <h2>Sonuç: {result.url}</h2>

                    <ScanSummary scan={result.scan} />

                    {result.report && (
                        <article className="report">
                            <Markdown source={result.report} />
                        </article>
                    )}

                    <details className="raw">
                        <summary>Ham tarama verisi (JSON)</summary>
                        <pre>{JSON.stringify(result.scan, null, 2)}</pre>
                    </details>
                </section>
            )}
        </main>
    );
}

export default App;
