import os
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="swell FastAPI demo", version="1.0.0")
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
            "region": os.getenv("DEMO_REGION", "local"), "framework": "FastAPI"}


@app.get("/api/hello")
def hello(name: str = Query(default="swell", max_length=100)):
    return {"message": f"안녕하세요, {name.strip() or 'swell'}! FastAPI 서버에서 보낸 응답입니다."}


class EchoInput(BaseModel):
    message: str = Field(min_length=1, max_length=500)


@app.post("/api/echo")
def echo(body: EchoInput):
    return {"message": body.message, "length": len(body.message)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")), proxy_headers=False)
