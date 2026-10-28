#!/usr/bin/python3
"""Restore user files from one installer backup, without changing packages."""
import argparse
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('backup', type=Path)
parser.add_argument('--home', type=Path, default=Path.home())
args = parser.parse_args()
backup = args.backup.resolve()
home = args.home.resolve()
manifest = backup / 'manifest.json'
records = json.loads(manifest.read_text()) if manifest.exists() else [json.loads(line) for line in (backup / 'journal.jsonl').read_text().splitlines()]
for record in reversed(records):
    relative = Path(record['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe path in backup manifest')
    target = home / relative
    parent = target.parent
    while parent != home:
        if parent.is_symlink():
            raise ValueError(f'Refusing symlinked destination: {parent}')
        parent = parent.parent
    if target.is_symlink() or target.is_file():
        target.unlink()
    if record['existed']:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup / relative, target, follow_symlinks=False)
print('User files restored. Log out and back in to restart the desktop.')
