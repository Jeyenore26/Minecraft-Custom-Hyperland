#!/usr/bin/python3
"""Session display presets for Super+P, with timed rollback."""
import fcntl
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
OPTIONS = ['Laptop only', 'Duplicate', 'Extend', 'External only']


def monitors():
    return json.loads(subprocess.check_output(['hyprctl', 'monitors', 'all', '-j']))


def apply(rules):
    def value(v):
        return str(v).lower() if isinstance(v, bool) else json.dumps(v)
    code = '\n'.join('hl.monitor({' + ','.join(
        k + '=' + value(v) for k, v in rule.items()) + '})' for rule in rules)
    result = subprocess.run(['hyprctl', 'eval', code], capture_output=True, text=True, timeout=10)
    if result.returncode or result.stdout.strip() != 'ok':
        raise RuntimeError(result.stderr or result.stdout or 'Display update failed')


def snapshot(outputs):
    rules = []
    for m in outputs:
        rule = dict(output=m['name'], disabled=m.get('disabled', False),
                    mode=f"{m['width']}x{m['height']}@{m['refreshRate']:.5f}",
                    position=f"{m['x']}x{m['y']}", scale=m['scale'],
                    transform=m['transform'], mirror='')
        if rule['disabled']:
            rule['mode'] = 'preferred'
        if m.get('mirrorOf', 'none') != 'none':
            rule['mirror'] = m['mirrorOf']
        rules.append(rule)
    # Enable sources before mirrors; disable unused outputs last.
    return sorted(rules, key=lambda r: (r['disabled'], bool(r['mirror'])))


def preset(choice, outputs):
    internal = next((m for m in outputs if m['name'].startswith(('eDP-', 'LVDS-', 'DSI-'))), None)
    external = [m for m in outputs if m is not internal]
    if choice in ('Laptop only', 'Duplicate') and internal is None:
        raise ValueError('No laptop display was detected.')
    if choice in ('Duplicate', 'External only') and not external:
        raise ValueError('Connect an external display first.')
    ordered = ([internal] if internal else []) + external
    rules = []
    for m in ordered:
        disabled = (choice == 'Laptop only' and m is not internal) or (choice == 'External only' and m is internal)
        rules.append(dict(output=m['name'], mode='preferred', position='auto',
                          scale=1, transform=0, disabled=disabled,
                          mirror=internal['name'] if choice == 'Duplicate' and m is not internal else ''))
    return sorted(rules, key=lambda r: (r['disabled'], bool(r['mirror'])))


def main():
    lock_path = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')) / f'minecraft-displays-{os.getuid()}.lock'
    with lock_path.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        menu = subprocess.run([
            'wofi', '--conf', '/dev/null', '--dmenu', '--prompt', 'Display options',
            '--style', str(ROOT / 'wofi.css'), '--width', '520', '--height', '390',
            '--insensitive', '--hide-scroll', '--cache-file', '/dev/null',
        ], input='\n'.join(OPTIONS), text=True, capture_output=True)
        choice = menu.stdout.strip()
        if menu.returncode or choice not in OPTIONS:
            return
        outputs = monitors()
        rules = preset(choice, outputs)
        previous = snapshot(outputs)
        keep = False
        try:
            apply(rules)
            confirmation = subprocess.run([
                'zenity', '--question', '--title=Display options',
                '--text=Keep this display layout?\nReverting in 15 seconds unless confirmed.',
                '--ok-label=Keep', '--cancel-label=Revert', '--timeout=15',
            ], timeout=18)
            keep = confirmation.returncode == 0
        finally:
            if not keep:
                apply(previous)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        subprocess.run(['zenity', '--error', '--title=Display options', '--text=' + str(error)])
