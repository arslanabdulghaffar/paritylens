import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def check_startup() -> dict:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "-B", "-m", "streamlit", "run", "app.py",
                                    "--server.headless", "true", "--server.address", "127.0.0.1",
                                    "--server.port", str(port)], cwd=ROOT, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Streamlit exited before startup")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("Streamlit health endpoint did not become ready")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError("Streamlit page failed")
            log.flush()
            log.seek(0)
            if "Traceback" in log.read():
                raise RuntimeError("Streamlit startup traceback")
            return {"headless_startup": "PASS", "health_http": 200, "page_http": 200,
                    "scope": "Local server startup/health only; Streamlit AppTest separately covers executed UI scenarios."}
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    print(json.dumps(check_startup(), indent=2))
