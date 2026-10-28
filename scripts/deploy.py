#!/usr/bin/python3
"""Render portable configuration, back up replaced files, and install as the user."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile

REPO = Path(__file__).resolve().parents[1]


def render(path, home):
    text = path.read_text()
    # Waybar command strings are executed by a shell; JSON itself needs JSON escaping.
    if path.name == 'waybar.json':
        def walk(value):
            if isinstance(value, dict):
                return {k: walk(v) for k, v in value.items()}
            if isinstance(value, list):
                return [walk(v) for v in value]
            if isinstance(value, str):
                return value.replace('@HOME@', shlex.quote(str(home)))
            return value
        return json.dumps(walk(json.loads(text)), indent=2) + '\n'
    if path.suffix == '.css':
        return text.replace('@HOME@', str(home).replace('\\', '\\\\').replace('"', '\\"'))
    # Hyprlang paths accept spaces in their values. Shell paths use $HOME.
    return text.replace('@HOME@', str(home))


def entries():
    mapping = {'config': '.config', 'share': '.local/share', 'bin': '.local/bin',
               'themes': '.themes', 'icons': '.icons'}
    for folder, destination in mapping.items():
        base = REPO / 'payload' / folder
        for source in sorted(base.rglob('*')):
            if source.is_file() or source.is_symlink():
                yield source, Path(destination) / source.relative_to(base)


def desktop_entry(home, script, title, icon):
    command = '/usr/bin/python3 "' + str(home / '.config/hypr/minecraft' / script).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$') + '"'
    category = 'Settings' if script == 'settings.py' else 'Utility'
    return f'[Desktop Entry]\nType=Application\nName={title}\nExec={command}\nIcon={icon}\nTerminal=false\nCategories={category};\n'


def deploy(home, dry_run=False):
    home = home.resolve()
    if any(c in str(home) for c in '\n\r@%"\\'):
        raise ValueError('Home directory contains characters unsupported by desktop/config formats')
    files = list(entries())
    generated = {
        Path('.local/share/applications/minecraft-settings.desktop'): desktop_entry(home, 'settings.py', 'Jeyenore System Settings', 'preferences-system'),
        Path('.local/share/applications/minecraft-field-guide.desktop'): desktop_entry(home, 'guide.py', 'Minecraft Desktop Guide', 'help-browser'),
    }
    if dry_run:
        print(f'Would install {len(files)} files and {len(generated)} launchers under {home}')
        print('Existing files are backed up; dependencies and login session require a normal installation.')
        return
    backup_base = home / '.local/state/jeyenore-hyprland/backups'
    backup_base.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_base))
    manifest = []

    def write(relative, source=None, text=None):
        target = home / relative
        # Refuse symlinked parent directories: backups must describe the actual destination.
        parent = target.parent
        while parent != home:
            if parent.is_symlink():
                raise ValueError(f'Refusing symlinked destination directory: {parent}')
            parent = parent.parent
        existed = target.exists() or target.is_symlink()
        if existed:
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved, follow_symlinks=False)
        manifest.append({'path': str(relative), 'existed': existed})
        with (backup / 'journal.jsonl').open('a') as journal:
            journal.write(json.dumps(manifest[-1]) + '\n')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        if source and source.is_symlink():
            target.unlink(missing_ok=True)
            target.symlink_to(os.readlink(source))
        elif text is not None:
            target.write_text(text)
            target.chmod(source.stat().st_mode & 0o777 if source else 0o644)
        else:
            shutil.copy2(source, target)

    for source, relative in files:
        if source.is_symlink():
            write(relative, source)
        elif source.is_relative_to(REPO / 'payload/config'):
            write(relative, source, render(source, home))
        else:
            write(relative, source)
    for relative, text in generated.items():
        write(relative, text=text)
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Installed configuration. Backup: {backup}')
    return backup


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    deploy(args.home, args.dry_run)
