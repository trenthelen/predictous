"""Temporary directory utilities."""

import os
import shutil
import stat
import tempfile
from pathlib import Path


def create_temp_dir(prefix: str = "sandbox_", base_dir: Path | None = None) -> Path:
    """Create a temporary directory for sandbox execution."""
    if base_dir is not None:
        base_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix=prefix, dir=str(base_dir))
    else:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
    return Path(temp_dir)


def cleanup_temp_dir(temp_path: Path) -> None:
    """Clean up a temporary directory, handling permission issues."""
    if not temp_path.exists():
        return

    try:
        # Make files writable before removal (Docker may have changed permissions)
        for root, dirs, files in os.walk(temp_path):
            root_path = Path(root)
            try:
                os.chmod(root_path, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
            except Exception:
                pass
            for d in dirs:
                try:
                    os.chmod(root_path / d, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
                except Exception:
                    pass
            for f in files:
                try:
                    os.chmod(root_path / f, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
                except Exception:
                    pass

        shutil.rmtree(temp_path, ignore_errors=True)
    except Exception:
        pass
