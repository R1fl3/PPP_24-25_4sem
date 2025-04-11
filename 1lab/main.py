import os
from dotenv import load_dotenv
from server import AudioServer
from client import AudioClient

load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8888))

if __name__ == '__main__':
    mode = input("Запустить сервер или клиент? (server/client): ")
    if mode == "server":
        server = AudioServer(host=HOST, port=PORT)
        server.run()
    elif mode == "client":
        client = AudioClient(host=HOST, port=PORT)
        client.run()
    else:
        print("Ошибка! Укажите server/client!")
