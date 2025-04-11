import os
import json
import socket
import tempfile
import logging
import select
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
AUDIO_DIR = "audio_files"
METADATA_FILE = "metadata.json"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 65432))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class AudioServer:
    def __init__(self, host, port):
        self.address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.inputs = [self.server_socket]
        self.client_buffers = {}

    def generate_metadata(self):
        metadata = []
        for file in os.listdir(AUDIO_DIR):
            if file.endswith(".mp3") or file.endswith(".wav"):
                file_path = os.path.join(AUDIO_DIR, file)
                audio = AudioSegment.from_file(file_path)
                metadata.append({
                    "name": file,
                    "duration": len(audio) / 1000,
                    "format": file.split('.')[-1]
                })

        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)
        logging.info("Метаданные обновлены.")

    def handle_request(self, sock, data):
        try:
            command = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            logging.warning(f"[{sock.getpeername()}] Некорректный JSON")
            sock.send(json.dumps({"error": "Некорректный формат запроса"}).encode("utf-8"))
            return

        if command["action"] == "list":
            logging.info(f"[{sock.getpeername()}] Запрос списка файлов")
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                response = f.read()
            sock.send(response.encode('utf-8'))

        elif command["action"] == "cut":
            file = command["file"]
            file_path = os.path.join(AUDIO_DIR, file)

            logging.info(f"[{sock.getpeername()}] Запрос обрезки файла '{file}'")

            if not os.path.exists(file_path):
                logging.error(f"[{sock.getpeername()}] Ошибка: Файл '{file}' не найден")
                sock.send(
                    json.dumps({"error": "Файл не найден. Проверьте название и повторите попытку."}).encode("utf-8"))
                return

            try:
                start = int(command["start"])
                end = int(command["end"])
            except ValueError:
                logging.error(f"[{sock.getpeername()}] Ошибка: Введены некорректные временные значения")
                sock.send(json.dumps({"error": "Временные значения должны быть целыми числами."}).encode("utf-8"))
                return

            audio = AudioSegment.from_file(file_path)
            duration = len(audio) // 1000

            if start < 0 or end < 0:
                logging.error(f"[{sock.getpeername()}] Ошибка: Время не может быть отрицательным")
                sock.send(json.dumps({"error": "Время не может быть отрицательным."}).encode("utf-8"))
                return
            if start >= duration:
                logging.error(
                    f"[{sock.getpeername()}] Ошибка: Начальное время {start} выходит за пределы ({duration} сек)")
                sock.send(
                    json.dumps({"error": f"Начальное время выходит за пределы длительности ({duration} сек)."}).encode(
                        "utf-8"))
                return
            if end > duration:
                logging.error(
                    f"[{sock.getpeername()}] Ошибка: Конечное время {end} выходит за пределы ({duration} сек)")
                sock.send(
                    json.dumps({"error": f"Конечное время выходит за пределы длительности ({duration} сек)."}).encode(
                        "utf-8"))
                return
            if start >= end:
                logging.error(f"[{sock.getpeername()}] Ошибка: Начальное время {start} >= конечного {end}")
                sock.send(
                    json.dumps({"error": "Начальное время не может быть больше или равно конечному."}).encode("utf-8"))
                return

            logging.info(f"[{sock.getpeername()}] Обрезка файла '{file}' с {start} сек до {end} сек")
            segment = audio[start * 1000:end * 1000]

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.split('.')[-1]}") as temp_file:
                segment.export(temp_file.name, format=file.split('.')[-1])
                temp_file.close()

                with open(temp_file.name, "rb") as f:
                    sock.sendall(f.read())
                os.unlink(temp_file.name)

            logging.info(f"[{sock.getpeername()}] Отправлен обрезанный файл '{file}' ({start}-{end} сек)")

    def run(self):
        self.generate_metadata()
        self.server_socket.bind(self.address)
        self.server_socket.listen()
        self.server_socket.setblocking(False)
        logging.info(f"Сервер запущен на {self.address[0]}:{self.address[1]}")

        while True:
            readable, _, exceptional = select.select(self.inputs, [], self.inputs)
            for sock in readable:
                if sock is self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    logging.info(f"Новое подключение от {addr}")
                    client_socket.setblocking(False)
                    self.inputs.append(client_socket)
                    self.client_buffers[client_socket] = b""
                else:
                    try:
                        data = sock.recv(4096)
                        if data:
                            self.handle_request(sock, data)
                        else:
                            self.inputs.remove(sock)
                            sock.close()
                            del self.client_buffers[sock]
                            logging.info(f"Клиент отключен")
                    except Exception as e:
                        logging.error(f"Ошибка при приеме данных: {e}")
                        self.inputs.remove(sock)
                        sock.close()

            for sock in exceptional:
                self.inputs.remove(sock)
                sock.close()
                logging.warning("Закрытие неисправного сокета")


if __name__ == "__main__":
    server = AudioServer(HOST, PORT)
    server.run()
