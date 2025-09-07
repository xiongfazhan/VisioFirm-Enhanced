import socket
import threading
import webbrowser
import waitress 
from visiofirm import create_app
import multiprocessing

app = create_app()

def find_free_port(start_port=8000):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                port += 1 

def main():
    port = find_free_port()
    url = f"http://localhost:{port}"
    
    print(r"""
WELCOME TO
 _   _ _____ _____ _____ ____  _____ _____ _____ 
 __      ___     _       ______ _                
 \ \    / (_)   (_)     |  ____(_)               
  \ \  / / _ ___ _  ___ | |__   _ _ __ _ __ ___  
   \ \/ / | / __| |/ _ \|  __| | | '__| '_ ` _ \ 
    \  /  | \__ \ | (_) | |    | | |  | | | | | |
     \/   |_|___/_|\___/|_|    |_|_|  |_| |_| |_|                          
 
You are currently running the version:
VisioFirm v0.2.0

Stay updated by visiting our GitHub Repository https://github.com/OschAI/VisioFirm
""".format(port=port))
    
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    threads = max(4, multiprocessing.cpu_count() * 2) 
    waitress.serve(app, host="localhost", port=port, threads=threads)

if __name__ == "__main__":
    main()