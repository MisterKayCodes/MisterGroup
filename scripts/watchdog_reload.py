# Made by Mister 💛
import sys
import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

class ReloadHandler(FileSystemEventHandler):
    """The 'Mirror Nervous System' for HOT RELOAD."""
    
    def __init__(self, command):
        self.command = command
        self.process = None
        self._start_process()

    def _start_process(self):
        """Wakes up the Organism (Bot)."""
        if self.process:
            logger.info("🛑 Terminating existing bot process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        logger.info(f"🚀 Starting Bot: {' '.join(self.command)}")
        # Transparently pass through stdout/stderr so we can see what's happening
        # Use a new process group on Windows if possible, or just standard Popen
        self.process = subprocess.Popen(
            self.command,
            cwd=os.getcwd(),
            bufsize=1,
            universal_newlines=True
        )

    def on_modified(self, event):
        """Re-birth on DNA change."""
        if event.is_directory: return
        
        # Only reload on .py file changes inside our project structure
        ext = os.path.splitext(event.src_path)[1]
        if ext == '.py' and '__pycache__' not in event.src_path:
            logger.info(f"🧬 DNA Change: {os.path.basename(event.src_path)}")
            self._start_process()

def main():
    """Watchdog - The Eternal Echo."""
    # Ensure logs folder exists
    if not os.path.exists("logs"): os.makedirs("logs")
    
    path = "."
    command = [sys.executable, "main.py"]
    
    # 2. Connection: Observe the directory.
    event_handler = ReloadHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    
    logger.info("👀 WATCHDOG ACTIVE: Monitoring all layers for changes...")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()

if __name__ == "__main__":
    main()
