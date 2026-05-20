import os

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8080

# Proxy configuration
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8888

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INTERCEPTED_DIR = os.path.join(BASE_DIR, 'intercepted_files')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INTERCEPTED_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Buffer size for socket transfers
BUFFER_SIZE = 4096

# Database
DB_PATH = os.path.join(LOG_DIR, 'traffic.db')
CSV_PATH = os.path.join(LOG_DIR, 'traffic.csv')
JSON_PATH = os.path.join(LOG_DIR, 'traffic.json')
