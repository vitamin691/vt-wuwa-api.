"""
vT Wuthering Waves Universe API
Starter API for connecting a website to your Python Discord bot.

Run:
    pip install -r requirements-api.txt
    uvicorn api:app --host 0.0.0.0 --port 8000

API docs (when running locally):
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="vT WuWa API",
    description="Starter API for the Wuthering Waves Universe project.",
    version="1.0.0",
)

# Replace "*" with your exact website origin before deploying publicly.
# Example: ["https://vitamin691.github.io"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
async def home():
    return {
        "developer": "vT Official",
        "project": "Wuthering Waves Universe",
        "status": "online",
        "message": "API is running.",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/character/{name}")
async def get_character(name: str):
    # Starter example only. Later, replace this with a database lookup.
    return {
        "character": name,
        "project": "Wuthering Waves Universe",
        "message": f"Welcome to {name}'s profile!",
    }
