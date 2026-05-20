import time
import threading

class TrafficMonitor:
    def __init__(self):
        self.total_bytes_up = 0
        self.total_bytes_down = 0
        self.active_sessions = 0
        self.total_requests = 0
        self.lock = threading.Lock()
        
        # For speed calculation
        self.last_bytes_up = 0
        self.last_bytes_down = 0
        self.last_time = time.time()
        self.up_speed = 0
        self.down_speed = 0
        
    def add_bytes_up(self, count):
        with self.lock:
            self.total_bytes_up += count
            
    def add_bytes_down(self, count):
        with self.lock:
            self.total_bytes_down += count
            
    def increment_requests(self):
        with self.lock:
            self.total_requests += 1
            
    def update_sessions(self, delta):
        with self.lock:
            self.active_sessions += delta
            
    def update_speeds(self):
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_time
            if elapsed >= 1.0:
                self.up_speed = (self.total_bytes_up - self.last_bytes_up) / elapsed
                self.down_speed = (self.total_bytes_down - self.last_bytes_down) / elapsed
                
                self.last_bytes_up = self.total_bytes_up
                self.last_bytes_down = self.total_bytes_down
                self.last_time = current_time

monitor = TrafficMonitor()
