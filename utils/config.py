import os

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8080

# Proxy configuration
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8888

# FTP Configuration
FTP_SERVER_PORT = 2121
FTP_PROXY_PORT = 2122

# Secure Configuration (HTTPS / FTPS)
HTTPS_SERVER_PORT = 8443
HTTPS_PROXY_PORT = 8843
FTPS_SERVER_PORT = 990
FTPS_PROXY_PORT = 9900

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INTERCEPTED_DIR = os.path.join(BASE_DIR, 'intercepted_files')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
CERTS_DIR = os.path.join(BASE_DIR, 'certs')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INTERCEPTED_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CERTS_DIR, exist_ok=True)

# Certificate paths
SERVER_CERT = os.path.join(CERTS_DIR, 'server.crt')
SERVER_KEY = os.path.join(CERTS_DIR, 'server.key')
PROXY_CERT = os.path.join(CERTS_DIR, 'proxy.crt')
PROXY_KEY = os.path.join(CERTS_DIR, 'proxy.key')

# Buffer size for socket transfers
BUFFER_SIZE = 4096

# Database
DB_PATH = os.path.join(LOG_DIR, 'traffic.db')
CSV_PATH = os.path.join(LOG_DIR, 'traffic.csv')
JSON_PATH = os.path.join(LOG_DIR, 'traffic.json')
