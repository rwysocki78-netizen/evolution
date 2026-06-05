from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.simulations import router as simulations_router

app = FastAPI(title="Evolution", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulations_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
