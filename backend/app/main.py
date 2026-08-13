from fastapi import FastAPI
from app.api.routes import router


app = FastAPI(
    title="AI Security Analyzer",
    description="Web security scanner with local AI reporting",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "AI Security Analyzer API is running"
    }