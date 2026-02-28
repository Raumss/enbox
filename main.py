"""
Enbox - Aggregate content from multiple platforms into one page.
"""

import asyncio
import yaml
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from fetchers import get_all_feeds


CONFIG_PATH = os.environ.get("ENBOX_CONFIG", "config.yaml")


def load_config() -> dict:
    p = Path(CONFIG_PATH)
    if not p.exists():
        p = Path("config.example.yaml")
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global config
    config = load_config()
    yield


app = FastAPI(title="Enbox", lifespan=lifespan)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/feeds")
async def api_feeds():
    """Return aggregated feeds as JSON."""
    global config
    if not config:
        config = load_config()
    sources = config.get("sources", [])
    results = await get_all_feeds(sources)
    return JSONResponse(content=results)


@app.get("/api/config")
async def api_config():
    """Return source config (names & types only) for the frontend."""
    global config
    if not config:
        config = load_config()
    sources = config.get("sources", [])
    return JSONResponse(content=[
        {"name": s.get("name", ""), "type": s.get("type", ""), "icon": s.get("icon", "")}
        for s in sources
    ])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
