import os
import re
import math
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="PADO Write API", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.middleware("http")
async def no_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/api/", "/health")):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "swell-demo-fastapi"}


@app.get("/api/info")
def info():
    # Only these explicitly public demo fields are exposed, never the environment.
    return {"name": os.getenv("APP_NAME", "swell FastAPI demo"),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "region": os.getenv("DEMO_REGION", "local"), "framework": "FastAPI",
            "sourceCommit": os.getenv("APP_COMMIT_SHA", "unknown")}


@app.get("/api/hello")
def hello(name: str = Query(default="swell", max_length=100)):
    return {"message": f"안녕하세요, {name.strip() or 'swell'}! FastAPI 서버에서 보낸 응답입니다."}


class EchoInput(BaseModel):
    message: str = Field(min_length=1, max_length=500)


@app.post("/api/echo")
def echo(body: EchoInput):
    return {"message": body.message, "length": len(body.message)}


class AnalysisInput(BaseModel):
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Write some text before analyzing")
        return value


@app.post("/api/analyze")
def analyze(body: AnalysisInput):
    """Analyze submitted text without persisting it or sending it to a third party."""
    text = body.text
    words = text.split()
    sentences = [s for s in re.split(r"[.!?。！？]+", text) if s.strip()]
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    tokens = re.findall(r"[^\W\d_]{2,}", text.lower(), flags=re.UNICODE)
    stopwords = {"the", "and", "for", "with", "this", "that", "from", "are", "있는", "있다", "그리고", "하지만", "것이다", "수", "그", "이"}
    keywords = Counter(t for t in tokens if t not in stopwords).most_common(6)
    return {"words": len(words), "characters": len(text),
            "characters_no_spaces": len(re.sub(r"\s", "", text)),
            "sentences": len(sentences), "paragraphs": len(paragraphs),
            "reading_seconds": max(1, math.ceil(len(words) / 240 * 60)),
            "keywords": [{"word": word, "count": count} for word, count in keywords]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")), proxy_headers=False)
