#!/usr/bin/python3
"""Integration checks: install, rerun, portable paths, backups and restoration."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('deploy', REPO / 'scripts/deploy.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)

with tempfile.TemporaryDirectory(prefix='jeyenore-install-test-') as temp:
    home = Path(temp) / "friend's home"
    config = home / '.config/hypr/minecraft'
    config.mkdir(parents=True)
    (config / 'waybar.json').write_text('original config\n')
    # Dry run must not write anything.
    before = sorted(home.rglob('*'))
    deploy.deploy(home, dry_run=True)
    assert before == sorted(home.rglob('*'))
    backup = deploy.deploy(home)
    assert (backup / '.config/hypr/minecraft/waybar.json').read_text() == 'original config\n'
    bar = json.loads((config / 'waybar.json').read_text())[0]
    assert bar['custom/realm']['format'] == 'Jeyenore'
    assert 'custom/settings' in bar['modules-left']
    # Actually execute the rendered command, substituting a harmless script.
    (config / 'settings.py').write_text("from pathlib import Path\nPath(__file__).with_suffix('.worked').touch()\n")
    subprocess.run(bar['custom/settings']['on-click'], shell=True, check=True)
    assert (config / 'settings.worked').exists()
    for path in (home / '.config').rglob('*'):
        if path.is_file():
            assert '@HOME@' not in path.read_text(), path
            assert '/home/jeyenore' not in path.read_text(), path
    assert os.access(config / 'launcher.sh', os.X_OK)
    assert (home / '.local/share/minecraft-desktop/frozen-river.png').is_file()
    assert (home / '.local/share/minecraft-desktop/lock-village-3d/frames/0000.jpg').is_file()
    desktop = home / '.local/share/applications/minecraft-settings.desktop'
    subprocess.run(['desktop-file-validate', str(desktop)], check=True)
    # Rerun after an edit and verify that the second backup preserves it.
    (config / 'waybar.json').write_text('my edited config\n')
    second = deploy.deploy(home)
    assert (second / '.config/hypr/minecraft/waybar.json').read_text() == 'my edited config\n'
    subprocess.run(['/usr/bin/python3', str(REPO / 'scripts/restore.py'), str(second), '--home', str(home)], check=True)
    assert (config / 'waybar.json').read_text() == 'my edited config\n'
    subprocess.run(['/usr/bin/python3', str(REPO / 'scripts/restore.py'), str(backup), '--home', str(home)], check=True)
    assert (config / 'waybar.json').read_text() == 'original config\n'
    assert not desktop.exists()
print('PASS: isolated install, rerun, quoting, desktop launcher, backup and restore')
