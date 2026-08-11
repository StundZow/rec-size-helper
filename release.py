"""Builds the app exe + the glassmorphism installer, tags the release, and
publishes both to GitHub.

Usage:
    python release.py 1.2 "- Nouveau design\n- Corrections"

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

GH_FALLBACKS = [r"C:\Program Files\GitHub CLI\gh.exe"]


def find_gh() -> str:
    found = shutil.which("gh")
    if found:
        return found
    for path in GH_FALLBACKS:
        if Path(path).exists():
            return path
    print("GitHub CLI ('gh') introuvable. Installe-le puis authentifie-toi avec 'gh auth login'.")
    sys.exit(1)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=True, cwd=ROOT, **kwargs)


def build_all() -> tuple[Path, Path]:
    """Builds app + uninstaller + installer. Returns (app_exe, installer_exe)."""
    # 1. the application itself (also the auto-update payload)
    run([
        "pyinstaller", "--noconfirm", "--windowed", "--onefile", "--name", "RecSizeHelper",
        "--icon", str(ROOT / "rechelper" / "assets" / "icon.ico"),
        "--add-data", f"{ROOT / 'rechelper' / 'assets'};rechelper/assets",
        "--collect-all", "PySide6", str(ROOT / "main.py"),
    ])
    app_exe = ROOT / "dist" / "RecSizeHelper.exe"
    if not app_exe.exists():
        print("Build failed: app exe not found.")
        sys.exit(1)

    # 2. the uninstaller (small, lives inside the install folder)
    run([
        "pyinstaller", "--noconfirm", "--windowed", "--onefile", "--name", "uninstall",
        "--icon", str(ROOT / "rechelper" / "assets" / "icon.ico"),
        "--add-data", f"{ROOT / 'rechelper' / 'assets'};rechelper/assets",
        "--collect-all", "PySide6",
        "--distpath", str(ROOT / "dist_uninstall"),
        str(ROOT / "installer" / "uninstall_app.py"),
    ])
    uninstall_exe = ROOT / "dist_uninstall" / "uninstall.exe"
    if not uninstall_exe.exists():
        print("Build failed: uninstaller not found.")
        sys.exit(1)

    # 3. the installer, embedding both as payload
    run([
        "pyinstaller", "--noconfirm", "--windowed", "--onefile", "--name", "RecSizeHelperSetup",
        "--icon", str(ROOT / "rechelper" / "assets" / "icon.ico"),
        "--add-data", f"{ROOT / 'rechelper' / 'assets'};rechelper/assets",
        "--add-data", f"{app_exe};payload",
        "--add-data", f"{uninstall_exe};payload",
        "--collect-all", "PySide6",
        "--distpath", str(ROOT / "dist_installer"),
        str(ROOT / "installer" / "installer_app.py"),
    ])
    installer_exe = ROOT / "dist_installer" / "RecSizeHelperSetup.exe"
    if not installer_exe.exists():
        print("Build failed: installer not found.")
        sys.exit(1)

    shutil.rmtree(ROOT / "build", ignore_errors=True)
    return app_exe, installer_exe


def main():
    if len(sys.argv) < 2:
        print("Usage: python release.py <version> [notes]")
        sys.exit(1)

    version = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else f"Version {version}"

    gh = find_gh()

    from rechelper import update_config
    if not update_config.is_configured():
        print("rechelper/update_config.py n'a pas GITHUB_OWNER / GITHUB_REPO renseignes.")
        sys.exit(1)

    VERSION_FILE.write_text(f'VERSION = "{version}"\n', encoding="utf-8")
    print(f"Version bumped to {version}")

    app_exe, installer_exe = build_all()

    tag = f"v{version}"
    repo = f"{update_config.GITHUB_OWNER}/{update_config.GITHUB_REPO}"

    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Release {tag}"])
    run(["git", "tag", tag])
    run(["git", "push", "origin", "HEAD"])
    run(["git", "push", "origin", tag])

    run([
        gh, "release", "create", tag,
        str(app_exe), str(installer_exe),
        "--repo", repo,
        "--title", tag,
        "--notes", notes,
    ])

    print(f"\nRelease {tag} published to {repo}.")
    print("- RecSizeHelperSetup.exe -> premiere installation (installateur glassmorphism)")
    print("- RecSizeHelper.exe -> utilise en interne par l'auto-updater")


if __name__ == "__main__":
    main()
