import os
import json
import socket
import threading
import logging
from pydub import AudioSegment
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)

# Directory to store audio files
AUDIO_DIR = 'audio_files'
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# Function to get audio file metadata
def get_audio_metadata():
    audio_files = []
    for filename in os.listdir(AUDIO_DIR):
        if filename.endswith(('.mp3', '.wav', '.ogg')):
            audio = AudioSegment.from_file(os.path.join(AUDIO_DIR, filename))
            audio_files.append({
                'name': filename,
                'duration': len(audio) / 1000,  # duration in seconds
                'format': filename.split('.')[-1]
            })
    with open('metadata.json', 'w') as f:
        json.dump(audio_files, f)
    return audio_files

# Function to handle client connections
def handle_client(client_socket):
    while True:
        request = client_socket.recv(1024).decode()
        if request == 'LIST':
            audio_files = get_audio_metadata()
            client_socket.send(json.dumps(audio_files).encode())
        elif request.startswith('GET'):
            _, filename, start, end = request.split()
            start, end = int(start), int(end)
            audio = AudioSegment.from_file(os.path.join(AUDIO_DIR, filename))
            segment = audio[start * 1000:end * 1000]
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                segment.export(temp_file.name, format='wav')
                client_socket.sendfile(open(temp_file.name, 'rb'))
            os.remove(temp_file.name)
        else:
            break
    client_socket.close()

# Main server function
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    logging.info('Server listening on port 9999')
    while True:
        client_socket, addr = server.accept()
        logging.info(f'Accepted connection from {addr}')
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == '__main__':
    start_server()
