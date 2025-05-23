import asyncio
import websockets
import json
import argparse
import getpass
import requests
from colorama import Fore, Style, init as colorama_init
import logging
from celery import Celery

colorama_init()
logging.basicConfig(level=logging.INFO, format="%(message)s")

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

def get_token(email: str, password: str) -> str:
    response = requests.post(f"{API_URL}/api/auth/login/", json={"email": email, "password": password})
    response.raise_for_status()
    return response.json()["access_token"]

def format_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)

def color_block(label, color):
    return f"{color}{label}{Style.RESET_ALL}"

async def poll_status(task_id: str):
    await asyncio.sleep(2)
    result = celery_app.AsyncResult(task_id)

    while True:
        status = result.status

        if status in ["PENDING", "STARTED"]:
            print(color_block("[PROGRESS]", Fore.BLUE))
            print(json.dumps({
                "status": "PROGRESS",
                "task_id": task_id,
                "operation": "encode/decode",
                "progress": 50
            }, indent=2))
            await asyncio.sleep(2)
        elif status == "SUCCESS":
            print(color_block("[COMPLETED]", Fore.GREEN))
            print(json.dumps({
                "status": "COMPLETED",
                "task_id": task_id,
                "result": result.result
            }, indent=2))
            print("-" * 50)
            break
        elif status == "FAILURE":
            print(color_block("[ERROR]", Fore.RED))
            print(f"Task failed: {result.result}")
            break
        else:
            print(color_block("[UNKNOWN]", Fore.YELLOW))
            print(f"Status: {status}")
            break

async def send_and_poll(task, token):
    uri = f"{WS_URL}?token={token}"
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            await websocket.send(json.dumps(task))
            while True:
                message = await websocket.recv()
                try:
                    msg = json.loads(message)
                except json.JSONDecodeError:
                    print(color_block("[WARNING] Received non-JSON message", Fore.YELLOW))
                    print(message)
                    continue

                if msg.get("status") == "STARTED":
                    print(color_block("[STARTED]", Fore.CYAN))
                    print(format_json(msg))
                    print("-" * 50)
                    task_id = msg.get("task_id")
                    if task_id:
                        asyncio.create_task(poll_status(task_id))
                    break

                elif "decoded_text" in msg:
                    print(color_block("[DECODED]", Fore.MAGENTA))
                    print(format_json(msg))
                    print("-" * 50)
                    break

                elif msg.get("status") == "ERROR":
                    print(color_block("[ERROR]", Fore.RED))
                    print(format_json(msg))
                    print("-" * 50)
                    break

                else:
                    print(color_block("[UNKNOWN RESPONSE]", Fore.YELLOW))
                    print(format_json(msg))
                    print("-" * 50)
                    break
    except Exception as e:
        print(color_block("[DISCONNECTED]", Fore.RED))
        print(f"Reason: {e}")

async def run_interactive_session(token: str):
    print("\nAvailable commands: encode, decode, status, exit\n")
    while True:
        action = input("> ").strip().lower()
        if action == "exit":
            break

        elif action == "encode":
            text = input("Enter text: ")
            key = input("Enter key: ")
            task = {"action": "encode", "text": text, "key": key}
            await send_and_poll(task, token)

        elif action == "decode":
            encoded_data = input("Enter encoded base64: ")
            key = input("Enter key: ")
            try:
                huffman = input("Enter huffman codes (JSON): ")
                huffman_codes = json.loads(huffman)
            except json.JSONDecodeError:
                print(Fore.RED + "Invalid Huffman codes JSON." + Style.RESET_ALL)
                continue
            try:
                padding = int(input("Enter padding: "))
            except ValueError:
                print(Fore.RED + "Padding must be an integer." + Style.RESET_ALL)
                continue
            task = {
                "action": "decode",
                "encoded_data": encoded_data,
                "key": key,
                "huffman_codes": huffman_codes,
                "padding": padding
            }
            await send_and_poll(task, token)

        elif action == "status":
            task_id = input("Enter task_id: ").strip()
            await poll_status(task_id)

        else:
            print(Fore.YELLOW + "Unknown command." + Style.RESET_ALL)

def parse_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

async def run_task_sequence(token: str, tasks: list):
    for task in tasks:
        await send_and_poll(task, token)

def main():
    parser = argparse.ArgumentParser(description="CLI WebSocket Client for Encoding/Decoding")
    parser.add_argument("--script", help="Path to script file with JSON lines of tasks")
    args = parser.parse_args()

    print("Enter your credentials to authenticate:")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    try:
        token = get_token(email, password)
        print(Fore.GREEN + "Authenticated successfully." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Authentication failed: {e}" + Style.RESET_ALL)
        return

    if args.script:
        tasks = parse_file(args.script)
        asyncio.run(run_task_sequence(token, tasks))
    else:
        print(Fore.CYAN + "\nNo script provided. Entering interactive mode." + Style.RESET_ALL)
        asyncio.run(run_interactive_session(token))

if __name__ == "__main__":
    main()
