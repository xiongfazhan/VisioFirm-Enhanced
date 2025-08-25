import socket
import threading
import webbrowser
from visiofirm import create_app

app = create_app()

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def main():
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()  # Delay to let server start
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == "__main__":
    main()