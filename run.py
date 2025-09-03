import socket
import threading
import webbrowser
from visiofirm import create_app

app = create_app()

def find_free_port(start_port=8000):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                port += 1  # Increment port and try again

def main():
    port = find_free_port()
    url = f"http://localhost:{port}"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()  # Delay to let server start
    app.run(host='localhost', port=port, debug=False)

if __name__ == "__main__":
    main()
