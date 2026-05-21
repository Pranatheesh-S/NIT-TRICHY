import os
import sys
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import SERVER_HOST, FTP_SERVER_PORT, DATA_DIR
from rich.console import Console

console = Console()

def start_ftp_server():
    authorizer = DummyAuthorizer()
    
    # We create a dummy user with full read/write permissions to the DATA_DIR
    # permissions: e=change dir, l=list files, r=retrieve file, a=append, d=delete, f=rename, m=make dir, w=store a file
    authorizer.add_user("user", "12345", DATA_DIR, perm="elradfmw")
    
    handler = FTPHandler
    handler.authorizer = authorizer
    
    # Optional: banner
    handler.banner = "Welcome to the Custom FTP Server."
    
    server = FTPServer((SERVER_HOST, FTP_SERVER_PORT), handler)
    
    console.print(f"[bold blue]FTP Server listening on {SERVER_HOST}:{FTP_SERVER_PORT}[/bold blue]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("[yellow]FTP Server shutting down...[/yellow]")

if __name__ == "__main__":
    start_ftp_server()
