"""Stop only a child created by this application, including Windows venv redirectors."""
import os
import subprocess


def stop_owned_process(process):
    if process is None or process.poll() is not None:
        return
    if os.name == "nt":
        # Windows venv python.exe is a redirector that can own a second Python
        # process. Terminating only the redirector leaves the Engine/file handles.
        result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        if result.returncode and process.poll() is None:
            raise RuntimeError("could not stop the owned Windows child process tree")
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
