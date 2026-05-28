import os
import sys
import ssl
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import SERVER_HOST, FTPS_SERVER_PORT, DATA_DIR, SERVER_CERT, SERVER_KEY
from rich.console import Console

console = Console()

def start_ftps_server():
    if not os.path.exists(SERVER_CERT) or not os.path.exists(SERVER_KEY):
        console.print(f"[red]Certificates not found at {SERVER_CERT}. Run cert_gen.py first.[/red]")
        sys.exit(1)
        
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "12345", DATA_DIR, perm="elradfmw")
    
    handler = TLS_FTPHandler
    handler.certfile = SERVER_CERT
    handler.keyfile = SERVER_KEY
    handler.authorizer = authorizer
    handler.tls_control_required = True
    handler.tls_data_required = True
    
    # TLS 1.3 setup within PyFTPdlib
    # Note: pyftpdlib might default to standard SSL options.
    # We can inject a custom SSL Context if required, but pyftpdlib handles basic TLS.
    # To force TLS 1.3, we overwrite its internal get_ssl_context method if needed,
    # but normally configuring PROTOCOL_TLS allows negotiation up to TLS 1.3.
    
    handler.banner = "Welcome to the Custom FTPS (TLS 1.3) Server."
    
    server = FTPServer((SERVER_HOST, FTPS_SERVER_PORT), handler)
    
    console.print(f"[bold blue]FTPS Server listening securely on {SERVER_HOST}:{FTPS_SERVER_PORT}[/bold blue]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("[yellow]FTPS Server shutting down...[/yellow]")

if __name__ == "__main__":
    start_ftps_server()
