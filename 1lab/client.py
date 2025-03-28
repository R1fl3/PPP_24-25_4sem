import socket
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Function to connect to the server
def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 9999))
    return client

# Function to get the list of audio files
def get_audio_files(client):
    client.send('LIST'.encode())
    response = client.recv(4096).decode()
    audio_files = json.loads(response)
    return audio_files

# Function to request an audio segment
def request_audio_segment(client, filename, start, end):
    request = f'GET {filename} {start} {end}'
    client.send(request.encode())
    with open(f'received_{filename}', 'wb') as f:
        while True:
            data = client.recv(4096)
            if not data:
                break
            f.write(data)

if __name__ == '__main__':
    client = connect_to_server()
    audio_files = get_audio_files(client)
    logging.info(f'Available audio files: {audio_files}')
    # Example of requesting an audio segment
    request_audio_segment(client, 'example.mp3', 10, 20)
    client.close()
