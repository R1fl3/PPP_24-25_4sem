import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.tasks import encode_task

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            if request.get("action") == "encode":
                text = request["text"]
                key = request["key"]
                task = encode_task.delay(text, key)
                await websocket.send_text(f"Task submitted: {task.id}")

                while not task.ready():
                    await websocket.send_text("Progress: pending...")
                    await asyncio.sleep(1)

                try:
                    result = task.get(timeout=10)  # таймаут на всякий случай
                    if isinstance(result, dict):
                        await websocket.send_json(result)
                    else:
                        await websocket.send_text("Error: Invalid result format")
                except Exception as e:
                    await websocket.send_text(f"Error processing task: {str(e)}")
                    await websocket.close()
                    break

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.close()
