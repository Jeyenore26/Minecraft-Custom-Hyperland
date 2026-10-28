#!/usr/bin/python3
"""Search open Hyprland windows and focus the selected one."""
import fcntl
import json
import os
from pathlib import Path
import subprocess


def main():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    with (runtime / f"minecraft-windows-{os.getuid()}.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
        clients = [c for c in clients if c.get("mapped") and not c.get("hidden")]
        clients.sort(key=lambda c: c.get("focusHistoryID", 9999))
        choices = {}
        for i, client in enumerate(clients, 1):
            title = " ".join(client.get("title", "").split())
            app = " ".join(client.get("class", "").split())
            workspace = client["workspace"]["name"]
            label = f"{i}. [{workspace}] {app} — {title}"
            choices[label] = client["address"]
        if not choices:
            return
        selected = subprocess.run(
            ["wofi", "--conf", "/dev/null", "--dmenu", "--insensitive",
             "--style", str(Path(__file__).with_name("wofi.css")),
             "--prompt", "Open windows…", "--width", "850", "--height", "420",
             "--cache-file", "/dev/null", "--define", "allow_markup=false",
             "--define", "allow_images=false"],
            input="\n".join(choices), text=True, capture_output=True,
        )
        address = choices.get(selected.stdout.rstrip("\n"))
        if selected.returncode == 0 and address:
            selector = json.dumps(f"address:{address}")
            subprocess.run(
                ["hyprctl", "eval",
                 f"hl.dispatch(hl.dsp.focus({{ window = {selector} }})); "
                 f"hl.dispatch(hl.dsp.window.alter_zorder({{ window = {selector}, mode = 'top' }}))"],
                check=True,
            )


if __name__ == "__main__":
    main()
