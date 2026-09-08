"""Start the local CycleCare frontend, backend, and ML service."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "app" / "www"
ML_SERVICE = ROOT / "ml-service"
VENV_PYTHON = BACKEND / "venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))


def start(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    return subprocess.Popen(command, cwd=cwd, env=env, creationflags=flags)


def wait_for(url: str, timeout: float = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> int:
    processes: list[subprocess.Popen] = []
    env = os.environ.copy()
    env.setdefault("DJANGO_ENV", "dev")
    env.setdefault("ML_SERVICE_URL", "http://127.0.0.1:8001")
    env.setdefault("PYTHONUNBUFFERED", "1")

    try:
        processes.append(start([PYTHON, "-m", "http.server", "5500", "--directory", str(FRONTEND)], ROOT, env))
        processes.append(start([PYTHON, "manage.py", "runserver", "127.0.0.1:8000"], BACKEND, env))
        processes.append(start([PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001"], ML_SERVICE, env))

        frontend_ready = wait_for("http://127.0.0.1:5500/login.html")
        print("CycleCare services started:")
        print("  Frontend: http://127.0.0.1:5500/login.html")
        print("  Backend:  http://127.0.0.1:8000/api/docs/")
        print("  ML:       http://127.0.0.1:8001/health/")
        if frontend_ready:
            webbrowser.open("http://127.0.0.1:5500/login.html")
        print("Press Ctrl+C to stop all services.")

        while True:
            exited = [process for process in processes if process.poll() is not None]
            if exited:
                return max((process.returncode or 0) for process in exited)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping CycleCare services...")
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
