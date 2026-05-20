import time
import os
import sys
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from monitoring.traffic_monitor import monitor
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from utils.helpers import format_bytes

console = Console()

def generate_dashboard() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main")
    )
    
    # Header
    layout["header"].update(Panel(f"[bold cyan]Network Traffic Interception & Monitoring[/bold cyan]"))
    
    # Main metrics
    monitor.update_speeds()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim", width=20)
    table.add_column("Value")
    
    table.add_row("Active Sessions", str(monitor.active_sessions))
    table.add_row("Total Requests", str(monitor.total_requests))
    table.add_row("Total Uploaded", format_bytes(monitor.total_bytes_up))
    table.add_row("Total Downloaded", format_bytes(monitor.total_bytes_down))
    table.add_row("Upload Speed", f"{format_bytes(monitor.up_speed)}/s")
    table.add_row("Download Speed", f"{format_bytes(monitor.down_speed)}/s")
    
    layout["main"].update(Panel(table, title="Live Traffic Statistics"))
    
    return layout

def run_dashboard():
    # Only run dashboard if we aren't heavily logging to console
    # To prevent visual corruption, we could just clear console periodically
    # However, since proxy logs connection intercepted, rich Live manages it
    try:
        with Live(generate_dashboard(), refresh_per_second=2, screen=False) as live:
            while True:
                time.sleep(0.5)
                live.update(generate_dashboard())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run_dashboard()
