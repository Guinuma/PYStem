"""Background separation with streamed logs and cooperative process-tree cancellation."""
import os
import subprocess
import threading
import time

import psutil
from PySide6.QtCore import QThread, Signal

try:
    from .backends import run_separation
except ImportError:
    from backends import run_separation


class Cancelled(RuntimeError):
    pass


def kill_tree(process):
    try:
        parent = psutil.Process(process.pid)
        for child in reversed(parent.children(recursive=True)):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        parent.kill()
    except psutil.NoSuchProcess:
        pass
    process.wait()


class SeparationWorker(QThread):
    log = Signal(str)
    succeeded = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, audio, output, options, parent=None):
        super().__init__(parent)
        self.audio, self.output, self.options = audio, output, options
        self.stop_event = threading.Event()

    def cancel(self):
        self.stop_event.set()

    def run_command(self, command, *, check, env, timeout):
        if self.stop_event.is_set():
            raise Cancelled()
        env = dict(env, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                   errors="replace", creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

        def read_output():
            line = ""
            try:
                while char := process.stdout.read(1):
                    if char in "\r\n":
                        if line.strip():
                            self.log.emit(line.strip())
                        line = ""
                    else:
                        line += char
                if line.strip():
                    self.log.emit(line.strip())
            except (OSError, ValueError):
                pass

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        started = time.monotonic()
        try:
            while process.poll() is None:
                if self.stop_event.wait(0.1):
                    kill_tree(process)
                    raise Cancelled()
                if time.monotonic() - started >= timeout:
                    kill_tree(process)
                    raise subprocess.TimeoutExpired(command, timeout)
            if self.stop_event.is_set():
                raise Cancelled()
            if check and process.returncode:
                raise subprocess.CalledProcessError(process.returncode, command)
        finally:
            if process.poll() is None:
                kill_tree(process)
            reader.join(timeout=2)
            process.stdout.close()

    def run(self):
        try:
            result = run_separation(self.audio, self.output, self.options, runner=self.run_command)
        except Cancelled:
            self.cancelled.emit()
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit(str(result))
