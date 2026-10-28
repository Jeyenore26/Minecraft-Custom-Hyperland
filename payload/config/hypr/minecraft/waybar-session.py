#!/usr/bin/python3
"""Keep one Minecraft bar per output, including after display reconnections."""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import threading

ROOT = Path(__file__).resolve().parent


def duplicate_outputs(layers, pid):
    return [name for name, monitor in layers.items()
            if sum(layer.get('namespace') == 'waybar' and layer.get('pid') == pid
                   for level in monitor['levels'].values() for layer in level) > 1]


def stop_bar(bar):
    if bar.poll() is None:
        bar.terminate()
        try:
            bar.wait(timeout=3)
        except subprocess.TimeoutExpired:
            bar.kill()
            bar.wait()


def main():
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime / 'minecraft-waybar.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        stopped = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stopped.set())
        bar = None
        try:
            while not stopped.is_set():
                bar = subprocess.Popen(['waybar', '-c', str(ROOT / 'waybar.json'),
                                        '-s', str(ROOT / 'waybar.css')])
                while not stopped.wait(5):
                    if bar.poll() is not None:
                        break
                    try:
                        result = subprocess.run(['hyprctl', 'layers', '-j'],
                                                capture_output=True, text=True,
                                                check=True, timeout=2)
                        duplicates = duplicate_outputs(json.loads(result.stdout), bar.pid)
                    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                        continue
                    if duplicates:
                        print('Rebuilding duplicate bars on ' + ', '.join(duplicates), flush=True)
                        break
                stop_bar(bar)
                if stopped.wait(1):
                    break
        finally:
            if bar is not None:
                stop_bar(bar)


if __name__ == '__main__':
    main()
