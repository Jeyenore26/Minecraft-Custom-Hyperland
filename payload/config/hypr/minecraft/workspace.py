#!/usr/bin/python3
import json, subprocess, sys
n=int(sys.argv[1])
try:
    workspaces=json.loads(subprocess.check_output(['hyprctl','-j','workspaces']))
    monitors=json.loads(subprocess.check_output(['hyprctl','-j','monitors']))
    active=any(m['activeWorkspace']['id']==n for m in monitors)
    count=next((w['windows'] for w in workspaces if w['id']==n),0)
    print(json.dumps({'text':str(n),'class':'active' if active else ('occupied' if count else 'empty'),'tooltip':f'Workspace {n} · {count} open windows'}))
except (OSError,ValueError,KeyError,subprocess.CalledProcessError):
    print(json.dumps({'text':str(n),'class':'unavailable','tooltip':'Hyprland unavailable'}))
