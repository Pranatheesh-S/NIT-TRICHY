import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import LOG_DIR
from utils.helpers import get_timestamp
from rich.console import Console

console = Console()

LOG_FILE = os.path.join(LOG_DIR, 'traffic.log')

def log_event(event_type, details):
    timestamp = get_timestamp()
    log_entry = f"[{timestamp}] [{event_type}] {details}\n"
    
    # Print it
    console.print(f"[bold magenta][LOG - {event_type}][/bold magenta] {details}")
    
    # Save to file
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
