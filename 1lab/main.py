import subprocess
import time


def main():

    server = subprocess.Popen(['python3', 'server.py'])
    time.sleep(1)
    client = subprocess.Popen(['python3', 'client.py'])
    

if __name__ == "__main__":
    main()

