import asyncio
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings
from app.tasks import encode_task, decode_task
from celery.result import AsyncResult
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/")

active_connections = {}

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise ValueError()
        return email
    except (JWTError, ValueError):
        raise WebSocketDisconnect(code=1008)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        user = get_current_user(token)
        await websocket.accept()
        active_connections[user] = websocket

        while True:
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"status": "ERROR", "message": "Invalid JSON format"})
                continue

            if "action" in request:
                operation = request.get("action")
                task_id = str(uuid.uuid4())

                await websocket.send_json({
                    "status": "STARTED",
                    "task_id": task_id,
                    "operation": operation
                })

                if operation == "encode":
                    encode_task.apply_async(args=[request["text"], request["key"]], task_id=task_id)
                elif operation == "decode":
                    decode_task.apply_async(args=[
                        request["encoded_data"],
                        request["key"],
                        request["huffman_codes"],
                        request["padding"]
                    ], task_id=task_id)
                else:
                    await websocket.send_json({"status": "ERROR", "message": "Unknown operation"})
            elif "task_id" in request:
                task_id = request["task_id"]
                result = AsyncResult(task_id)
                operation = request.get("operation", "encode/decode")

                if result.state == "PENDING" or result.state == "STARTED":
                    await websocket.send_json({
                        "status": "PROGRESS",
                        "task_id": task_id,
                        "operation": operation,
                        "progress": 50
                    })
                elif result.state == "SUCCESS":
                    task_result = result.result
                    if isinstance(task_result, dict) and "decoded_text" in task_result:
                        await websocket.send_json(task_result)
                    else:
                        await websocket.send_json({
                            "status": "COMPLETED",
                            "task_id": task_id,
                            "operation": operation,
                            "result": task_result
                        })
                elif result.state == "FAILURE":
                    await websocket.send_json({"status": "ERROR", "message": str(result.result)})
                else:
                    await websocket.send_json({"status": result.state, "task_id": task_id})
            else:
                await websocket.send_json({"status": "ERROR", "message": "Invalid request format"})

    except WebSocketDisconnect:
        if user in active_connections:
            del active_connections[user]
    except Exception as e:
        await websocket.send_json({"status": "ERROR", "message": str(e)})
        await websocket.close()
