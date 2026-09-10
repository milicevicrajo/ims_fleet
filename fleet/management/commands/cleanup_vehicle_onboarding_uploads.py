import re
import time
from pathlib import Path
from django.core.management.base import BaseCommand
from fleet.views.vehicle_onboarding import STORAGE, TTL


class Command(BaseCommand):
    help = 'Uklanja privremene priloge isteklih unosa vozila (starije od dva sata i 15 minuta).'

    def handle(self, *args, **options):
        root = Path(STORAGE.location).resolve()
        removed = 0
        if root.exists():
            for folder in root.iterdir():
                if not re.fullmatch(r'[0-9a-f]{32}', folder.name) or folder.is_symlink() or not folder.is_dir():
                    continue
                if time.time() - folder.stat().st_mtime <= TTL + 15 * 60:
                    continue
                # Only delete direct files in a verified, task-owned temporary folder.
                if folder.resolve().parent != root:
                    continue
                for file in folder.iterdir():
                    if file.is_file() and not file.is_symlink() and file.resolve().parent == folder.resolve():
                        try:
                            file.unlink()
                            removed += 1
                        except OSError:
                            continue
                try:
                    folder.rmdir()
                except OSError:
                    pass
        self.stdout.write(f'Uklonjeno privremenih priloga: {removed}')
