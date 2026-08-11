"""Builds the exe, tags the release, and publishes it to GitHub.

Usage:
    python release.py 1.1 "- Suppression definitive\n- Auto-update"

Requires the GitHub CLI (`gh`) installed and authenticated (`gh auth login`),
and rechelper/update_config.py filled in with GITHUB_OWNER / GITHUB_REPO.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VERSION_FILE = ROOT / "rechelper" / "__version__.py"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=True, cwd=ROOT, **kwargs)


def main():
    if len(sys.argv) < 2:
        print("Usage: python release.py <version> [notes]")
        sys.exit(1)

    version = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else f"Version {version}"

    if not shutil.which("gh"):
        print(
            "GitHub CLI ('gh') introuvable. Installe-le (winget install GitHub.cli), "
            "puis authentifie-toi avec 'gh auth login' avant de relancer ce script."
        )
        sys.exit(1)

    from rechelper import update_config
    if not update_config.is_configured():
        print(
            "rechelper/update_config.py n'a pas encore GITHUB_OWNER / GITHUB_REPO renseignes. "
            "Remplis-les avant de publier une release."
        )
        sys.exit(1)

    VERSION_FILE.write_text(f'VERSION = "{version}"\n', encoding="utf-8")
    print(f"Version bumped to {version}")

    run([
        "pyinstaller", "--noconfirm", "--windowed", "--onefile", "--name", "RecSizeHelper",
        "--icon", str(ROOT / "rechelper" / "assets" / "icon.ico"),
        "--add-data", f"{ROOT / 'rechelper' / 'assets'};rechelper/assets",
        "--collect-all", "PySide6", str(ROOT / "main.py"),
    ])
    shutil.rmtree(ROOT / "build", ignore_errors=True)

    exe_path = ROOT / "dist" / "RecSizeHelper.exe"
    if not exe_path.exists():
        print("Build failed: exe not found.")
        sys.exit(1)

    tag = f"v{version}"
    repo = f"{update_config.GITHUB_OWNER}/{update_config.GITHUB_REPO}"

    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Release {tag}"])
    run(["git", "tag", tag])
    run(["git", "push", "origin", "HEAD"])
    run(["git", "push", "origin", tag])

    run([
        "gh", "release", "create", tag,
        str(exe_path),
        "--repo", repo,
        "--title", tag,
        "--notes", notes,
    ])

    print(f"\nRelease {tag} published to {repo}. RecSizeHelper.exe will now offer this update.")


if __name__ == "__main__":
    main()
