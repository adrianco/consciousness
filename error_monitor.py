#!/usr/bin/env python3
"""
Real-time Error Monitor for Consciousness Service
Monitors console output, log files, and service errors
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


class ErrorMonitor:
    def __init__(self):
        self.errors = []
        self.memory_key = "swarm-auto-centralized-1750878001490/error-monitor/errors"
        self.log_files = [
            "/workspaces/consciousness/sessions/claude-session-debug.log",
            "/workspaces/consciousness/sessions/claude-session-debug2.log",
            "/workspaces/consciousness/sessions/claude-session-debug3.log",
            "/workspaces/consciousness/consciousness.log",
            "/workspaces/consciousness/api.log",
        ]
        self.error_patterns = [
            r"ERROR",
            r"Error",
            r"error",
            r"Exception",
            r"exception",
            r"FAILED",
            r"Failed",
            r"failed",
            r"Traceback",
            r"Warning",
            r"WARNING",
            r"CRITICAL",
            r"Critical",
            r"500\s+Internal\s+Server\s+Error",
            r"404\s+Not\s+Found",
            r"TypeError",
            r"ValueError",
            r"KeyError",
            r"AttributeError",
            r"ImportError",
            r"ModuleNotFoundError",
            r"ConnectionError",
            r"TimeoutError",
        ]
        self.error_regex = re.compile("|".join(self.error_patterns), re.IGNORECASE)

    def monitor_service_startup(self):
        """Monitor the consciousness service startup"""
        print("[MONITOR] Checking for service startup...")

        # Check if service is already running
        try:
            result = subprocess.run(
                ["lsof", "-i", ":8000"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print("[MONITOR] Service already running on port 8000")
                return
        except:
            pass

        print("[MONITOR] Attempting to start consciousness service...")
        try:
            # Try different startup methods
            startup_commands = [
                "cd /workspaces/consciousness && uvicorn consciousness.main:app --host 0.0.0.0 --port 8000 --reload",
                "cd /workspaces/consciousness && python -m consciousness.main",
                "cd /workspaces/consciousness && ./start.sh",
                "cd /workspaces/consciousness && python consciousness/main.py",
            ]

            for cmd in startup_commands:
                print(f"[MONITOR] Trying: {cmd}")
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                time.sleep(3)  # Give it time to start

                if proc.poll() is None:  # Still running
                    print(f"[MONITOR] Service started with: {cmd}")
                    self.monitor_process_output(proc)
                    break
                else:
                    stdout, stderr = proc.communicate()
                    if stderr:
                        self.log_error(
                            {
                                "timestamp": datetime.now().isoformat(),
                                "source": "startup",
                                "command": cmd,
                                "error": stderr,
                                "stdout": stdout,
                            }
                        )

        except Exception as e:
            self.log_error(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "startup",
                    "error": str(e),
                    "type": type(e).__name__,
                }
            )

    def monitor_process_output(self, process):
        """Monitor stdout and stderr of a running process"""

        def read_output(pipe, pipe_name):
            for line in iter(pipe.readline, ""):
                if line:
                    print(f"[{pipe_name}] {line.strip()}")
                    if self.error_regex.search(line):
                        self.log_error(
                            {
                                "timestamp": datetime.now().isoformat(),
                                "source": f"process_{pipe_name}",
                                "message": line.strip(),
                            }
                        )

        stdout_thread = threading.Thread(
            target=read_output, args=(process.stdout, "STDOUT")
        )
        stderr_thread = threading.Thread(
            target=read_output, args=(process.stderr, "STDERR")
        )

        stdout_thread.start()
        stderr_thread.start()

    def monitor_log_files(self):
        """Monitor log files for errors"""
        print("[MONITOR] Starting log file monitoring...")

        # Track file positions
        file_positions = {}

        while True:
            for log_file in self.log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, "r") as f:
                            # Go to last position or start
                            if log_file in file_positions:
                                f.seek(file_positions[log_file])

                            # Read new lines
                            new_lines = f.readlines()

                            # Update position
                            file_positions[log_file] = f.tell()

                            # Check for errors
                            for line in new_lines:
                                if self.error_regex.search(line):
                                    self.log_error(
                                        {
                                            "timestamp": datetime.now().isoformat(),
                                            "source": f"log_file:{log_file}",
                                            "message": line.strip(),
                                        }
                                    )
                    except Exception as e:
                        print(f"[MONITOR] Error reading {log_file}: {e}")

            time.sleep(1)  # Check every second

    def monitor_web_interface(self):
        """Monitor web interface for errors"""
        print("[MONITOR] Checking web interface...")

        try:
            import requests

            response = requests.get("http://localhost:8000", timeout=5)
            if response.status_code != 200:
                self.log_error(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "source": "web_interface",
                        "status_code": response.status_code,
                        "url": "http://localhost:8000",
                        "response": response.text[:500],
                    }
                )
        except Exception as e:
            self.log_error(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": "web_interface",
                    "error": str(e),
                    "type": type(e).__name__,
                }
            )

    def log_error(self, error_data):
        """Log error to console and save to memory"""
        print(f"\n[ERROR DETECTED] {error_data['timestamp']}")
        print(f"Source: {error_data['source']}")
        print(f"Details: {json.dumps(error_data, indent=2)}")
        print("-" * 80)

        self.errors.append(error_data)
        self.save_to_memory()

    def save_to_memory(self):
        """Save errors to memory file"""
        memory_dir = Path("/workspaces/consciousness/memory/data")
        memory_dir.mkdir(parents=True, exist_ok=True)

        memory_file = memory_dir / f"{self.memory_key.replace('/', '_')}.json"

        try:
            with open(memory_file, "w") as f:
                json.dump(
                    {
                        "key": self.memory_key,
                        "total_errors": len(self.errors),
                        "last_updated": datetime.now().isoformat(),
                        "errors": self.errors,
                    },
                    f,
                    indent=2,
                )

            print(f"[MONITOR] Saved {len(self.errors)} errors to memory")
        except Exception as e:
            print(f"[MONITOR] Failed to save to memory: {e}")

    def run(self):
        """Run all monitoring tasks"""
        print("=" * 80)
        print("ERROR MONITOR STARTED")
        print(f"Monitoring key: {self.memory_key}")
        print("=" * 80)

        # Start monitoring threads
        threads = [
            threading.Thread(target=self.monitor_service_startup),
            threading.Thread(target=self.monitor_log_files),
        ]

        for thread in threads:
            thread.daemon = True
            thread.start()

        # Monitor web interface periodically
        while True:
            time.sleep(10)
            self.monitor_web_interface()


if __name__ == "__main__":
    monitor = ErrorMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n[MONITOR] Shutting down...")
        monitor.save_to_memory()
        sys.exit(0)
