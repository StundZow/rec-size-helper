"""Builds the exe + Windows installer, tags the release, and publishes it to GitHub.

Usage:
    python release.py 1.1 "- Suppression definitive\n- Auto-update"

Requires the GitHub CLI (`gh`) and Inno Setup, both installed and on PATH
(or in their usual install locations), plus rechelper/update_config.py
filled in with GITHUB_OWNER / GITHUB_REPO.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VERSION_FILE = ROOT / "rechelper" / "__version__.py"

GH_FALLBACKS = [r"C:\Program Files\GitHub CLI\gh.exe"]
ISCC_FALLBACKS = [
    str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe"),
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]


def find_tool(name: str, fallbacks: list[str]) -> str:
    found = shutil.which(name)
    if found:
        return found
    for path in fallbacks:
        if Path(path).exists():
            return path
    print(f"'{name}' introuvable. Verifie qu'il est installe.")
    sys.exit(1)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=True, cwd=ROOT, **kwargs)


def main():
    if len(sys.argv) < 2:
        print("Usage: python release.py <version> [notes]")
        sys.exit(1)

    version = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else f"Version {version}"

    gh = find_tool("gh", GH_FALLBACKS)
    iscc = find_tool("ISCC.exe", ISCC_FALLBACKS)

    from rechelper import update_config
    if not update_config.is_configured():
        print(
            "rechelper/update_config.py n'a pas encore GITHUB_OWNER / GITHUB_REPO renseignes. "
            "Remplis-les avant de publier une release."
        )
        sys.exit(1)

    VERSION_FILE.write_text(f'VERSION = "{version}"\n', encoding="utf-8")
    print(f"Version bumped to {version}")

    # 1. Build the portable exe (used both standalone and by the auto-updater).
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

    # 2. Wrap it in a proper installer (desktop icon + launch-after-install
    #    checkboxes, installs to %LocalAppData%\Programs so no admin needed).
    run([iscc, f"/DMyAppVersion={version}", str(ROOT / "installer.iss")])

    installer_path = ROOT / "dist_installer" / "RecSizeHelperSetup.exe"
    if not installer_path.exists():
        print("Build failed: installer not found.")
        sys.exit(1)

    tag = f"v{version}"
    repo = f"{update_config.GITHUB_OWNER}/{update_config.GITHUB_REPO}"

    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"Release {tag}"])
    run(["git", "tag", tag])
    run(["git", "push", "origin", "HEAD"])
    run(["git", "push", "origin", tag])

    run([
        gh, "release", "create", tag,
        str(exe_path), str(installer_path),
        "--repo", repo,
        "--title", tag,
        "--notes", notes,
    ])

    print(f"\nRelease {tag} published to {repo}.")
    print("- RecSizeHelperSetup.exe -> premiere installation")
    print("- RecSizeHelper.exe -> utilise en interne par l'auto-updater")


if __name__ == "__main__":
    main()
