import { useState } from "react";

function App() {
    // Kullanıcının girdiği URL
    const [url, setUrl] = useState("");

    // FastAPI'den dönen sonuç
    const [result, setResult] = useState(null);

    // Tarama devam ediyor mu?
    const [loading, setLoading] = useState(false);

    // -----------------------------------------------------
    // FASTAPI'YE TARAMA İSTEĞİ GÖNDER
    // -----------------------------------------------------

    const scanWebsite = async () => {
        // Eski sonucu temizle
        setResult(null);

        // Tarama başladı
        setLoading(true);

        try {
            const response = await fetch(
                "http://127.0.0.1:8000/scan",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify({
                        url: url,
                    }),
                }
            );

            // HTTP hatası varsa
            if (!response.ok) {
                throw new Error(
                    "FastAPI isteği başarısız oldu."
                );
            }

            // JSON cevabını al
            const data = await response.json();

            // Sonucu React state'e koy
            setResult(data);

        } catch (error) {

            console.error(error);

            setResult({
                error: error.message,
            });

        } finally {

            // Tarama bitti
            setLoading(false);
        }
    };

    // -----------------------------------------------------
    // ARAYÜZ
    // -----------------------------------------------------

    return (
        <div>
            <h1>AI Security Analyzer</h1>

            <input
                type="text"
                value={url}
                onChange={(event) =>
                    setUrl(event.target.value)
                }
                placeholder="https://example.com"
            />

            <button
                onClick={scanWebsite}
                disabled={loading}
            >
                {loading
                    ? "Tarama yapılıyor..."
                    : "Tara"}
            </button>

            {result && (
                <pre>
                    {JSON.stringify(
                        result,
                        null,
                        2
                    )}
                </pre>
            )}
        </div>
    );
}

export default App;