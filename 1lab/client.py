import socket
import json
import os
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 65432))

class AudioClient:
    def __init__(self, host, port):
        self.address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect(self.address)
        print(f"Подключен к серверу {self.address[0]}:{self.address[1]}")

    def send_command(self, command):
        self.client_socket.send(json.dumps(command).encode("utf-8"))

    def receive_json_data(self):
        data = b''
        while True:
            data += self.client_socket.recv(100)
            try:
                return json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
                # return {"error": "Ошибка обработки ответа от сервера."}

    def list_files(self):
        self.send_command({"action": "list"})
        response = self.receive_json_data()

        if "error" in response:
            print(f"Ошибка: {response['error']}")
        else:
            files = response if isinstance(response, list) else []
            if files:
                print("Доступные файлы:")
                for file in files:
                    print(f"- {file['name']} ({file['duration']} сек.)")
            else:
                print("Нет доступных файлов.")

    def cut_audio(self):
        self.send_command({"action": "list"})
        files_data = self.receive_json_data()

        if "error" in files_data:
            print(f"Ошибка: {files_data['error']}")
            return

        available_files = {file["name"]: file["duration"] for file in files_data}

        file = input("Имя файла: ").strip()
        if file not in available_files:
            print(f"Ошибка: Файл '{file}' не найден. Доступные файлы: {', '.join(available_files.keys())}")
            return

        duration = available_files[file]

        try:
            start = int(input("Начальное время (сек): "))
            end = int(input("Конечное время (сек): "))
        except ValueError:
            print("Ошибка: Время должно быть числом.")
            return

        if start < 0 or end < 0:
            print("Ошибка: Время не может быть отрицательным.")
            return
        if start >= duration:
            print(f"Ошибка: Начальное время выходит за пределы длительности файла ({duration} сек).")
            return
        if end > duration:
            print(f"Ошибка: Конечное время выходит за пределы длительности файла ({duration} сек).")
            return
        if start >= end:
            print("Ошибка: Начальное время не может быть больше или равно конечному.")
            return

        self.send_command({"action": "cut", "file": file, "start": start, "end": end})
        first_chunk = self.client_socket.recv(4096)

        try:
            decoded = first_chunk.decode("utf-8")
            if decoded.startswith('{"error"'):
                error_msg = json.loads(decoded)["error"]
                print("Ошибка:", error_msg)
                return
        except UnicodeDecodeError:
            pass

        filename = f"cut_{file}"
        with open(filename, "wb") as f:
            f.write(first_chunk)
            self.client_socket.settimeout(1.0)
            try:
                while True:
                    chunk = self.client_socket.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
            except socket.timeout:
                pass

        self.client_socket.settimeout(None)
        print(f"Аудио отрезок сохранен как {filename}")

    def run(self):
        self.connect()
        try:
            while True:
                cmd = input("Введите команду (list/cut/exit): ").strip().lower()
                if cmd == "list":
                    self.list_files()
                elif cmd == "cut":
                    self.cut_audio()
                elif cmd == "exit":
                    break
                else:
                    print("Неизвестная команда.")
        finally:
            self.client_socket.close()
            print("Отключено от сервера.")


if __name__ == "__main__":
    client = AudioClient(HOST, PORT)
    client.run()
