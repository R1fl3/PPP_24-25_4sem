from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.encryption import router as encryption_router
from app.api.websocket import router as ws_router
import subprocess
import time

app = FastAPI(title="Encryption API")

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(encryption_router, prefix="/api/encryption", tags=["Encryption"])
app.include_router(ws_router, tags=["WebSocket"])
