#!/usr/bin/python3
"""Play pre-rendered village frames inside native Hyprlock's locked surface.

Hyprlock owns authentication and the Wayland session lock. This controller only
selects image paths and sends SIGUSR2 after Hyprlock installs its signal handler.
If playback stops, the last frame stays visible and Hyprlock stays locked.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ASSETS = Path.home()/'.local/share/minecraft-desktop/lock-village-3d'
CONFIG = Path.home()/'.config/hypr/minecraft/hyprlock.conf'
RELOAD = 'cat "$XDG_RUNTIME_DIR/minecraft-lock-village/frame-path"'


def write_atomic(path, value):
    temporary = path.with_suffix('.next')
    temporary.write_text(value)
    temporary.replace(path)


def catches_refresh(pid):
    try:
        for line in Path(f'/proc/{pid}/status').read_text().splitlines():
            if line.startswith('SigCgt:'):
                return bool(int(line.split()[1],16) & (1 << (signal.SIGUSR2-1)))
    except (FileNotFoundError, ProcessLookupError):
        pass
    return False


def outputs_awake():
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return True
    try:
        result = subprocess.run(['hyprctl','-j','monitors'],capture_output=True,text=True,timeout=1)
        monitors = json.loads(result.stdout)
        return any(m.get('dpmsStatus',True) for m in monitors)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--runtime-dir',type=Path)
    args=parser.parse_args()
    root=args.runtime_dir or Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}'))/'minecraft-lock-village'
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    guard=open(root/'launcher.lock','w')
    try:
        fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    conf=args.config.read_text()
    try:
        info=json.loads((ASSETS/'animation.json').read_text())
        fps=min(24,max(1,int(info['fps'])))
        frames=[ASSETS/'frames'/f'{i:04d}.jpg' for i in range(int(info['frames']))]
        if not frames or not all(p.is_file() for p in frames):
            raise ValueError('Incomplete animation frames')
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'Animation unavailable; using still lock screen: {error}',flush=True)
        frames=[]
        conf='\n'.join(line for line in conf.splitlines() if not line.strip().startswith(('reload_time =','reload_cmd =')))+'\n'
    if frames:
        # Runtime path is controlled by us; quote it for Hyprlock's command parser.
        quoted="'"+str(root/'frame-path').replace("'", "'\\''")+"'"
        conf=conf.replace(RELOAD,'cat '+quoted)
        write_atomic(root/'frame-path',str(frames[0])+'\n')
    (root/'hyprlock.conf').write_text(conf)
    (root/'controller.pid').write_text(str(os.getpid()))
    try:
        lock=subprocess.Popen(['/usr/bin/hyprlock','--config',str(root/'hyprlock.conf')])
        (root/'hyprlock.pid').write_text(str(lock.pid))
        if not frames:
            return lock.wait()
        # SIGUSR2's default disposition is termination. Never send it during startup.
        while lock.poll() is None and not catches_refresh(lock.pid):
            time.sleep(.05)
        start=time.monotonic()
        next_power_check=0
        awake=True
        last_index=-1
        while lock.poll() is None:
            now=time.monotonic()
            if now>=next_power_check:
                awake=outputs_awake()
                next_power_check=now+3
            if not awake:
                time.sleep(.5)
                continue
            index=int((now-start)*fps)%len(frames)
            if index!=last_index:
                write_atomic(root/'frame-path',str(frames[index])+'\n')
                try:
                    os.kill(lock.pid,signal.SIGUSR2)
                except ProcessLookupError:
                    break
                last_index=index
            time.sleep(max(.005,1/fps-((time.monotonic()-start)%(1/fps))))
        return lock.wait()
    finally:
        # Never signal unlock or terminate the locker from this controller.
        for name in ['controller.pid','hyprlock.pid','frame-path','frame-path.next','hyprlock.conf']:
            (root/name).unlink(missing_ok=True)

if __name__=='__main__':
    raise SystemExit(main())
