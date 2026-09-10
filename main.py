import os
import subprocess
import sys
import time

# Emoji utilisés par l'interface : rendus une fois ici, avant la fenêtre, pour que le
# chargement de la police emoji (~1 s) tombe sur une vraie étape de la barre de
# progression au lieu de geler la première peinture de la fenêtre.
_UI_EMOJI = "🎬📁📌⚙️🔒🔓☀🌙🗑️💾🛡️🚀✅❌⚠️✓✕◀▶"


def _mark(label: str):
    """Diagnostic de démarrage, actif seulement si RSH_TIMING pointe vers un fichier :
    note le temps écoulé depuis la création du processus à chaque étape du lancement.

    En build onefile, ce code tourne dans un processus *enfant* du bootloader, créé une
    fois l'archive extraite : la référence est alors le parent (même exe), pour que ces
    marques soient comparables à un chronomètre extérieur déclenché au double-clic."""
    log_path = os.environ.get("RSH_TIMING")
    if not log_path:
        return
    import psutil

    process = psutil.Process()
    parent = process.parent()
    if getattr(sys, "frozen", False) and parent is not None and parent.name() == process.name():
        process = parent
    elapsed = time.time() - process.create_time()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{elapsed:7.3f}s  {label}\n")


class _Splash:
    """L'écran de lancement tourne dans un second processus (voir rechelper/splash.py) :
    on lui envoie l'avancement par son entrée standard. S'il a disparu, on continue sans lui."""

    def __init__(self):
        env = None
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--splash"]
            # Build onefile : sans ça, le second processus ré-extrairait toute l'archive
            # avant d'afficher quoi que ce soit. Le bootloader PyInstaller lit _MEIPASS2
            # pour tourner directement depuis le dossier déjà extrait par ce processus-ci,
            # qui lui survit (le splash se ferme toujours avant l'appli).
            env = {**os.environ, "_MEIPASS2": sys._MEIPASS}
        else:
            command = [sys.executable, os.path.abspath(__file__), "--splash"]
        try:
            self._proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError:
            self._proc = None

    def progress(self, percent: int):
        self._send(f"progress {percent}")

    def done(self):
        self._send("done")

    def _send(self, message: str):
        if self._proc is None or self._proc.stdin is None:
            return
        try:
            self._proc.stdin.write(f"{message}\n".encode("utf-8"))
            self._proc.stdin.flush()
        except (OSError, ValueError):
            self._proc = None


def _place_window(window, screen):
    """Taille qui tient dans l'écran (la fenêtre ne calcule pas la sienne), et cadre
    centré là où est centré l'écran de lancement, pour que le passage de l'un à l'autre
    se fasse sans saut.

    winId() crée la fenêtre native sans l'afficher : c'est ce qui permet à
    frameGeometry() de connaître la barre de titre (~31 px) *avant* show(). Sans ça, le
    centrage se fait sur la zone client seule et la fenêtre atterrit ~20 px trop bas —
    ou, si on la recentre après show(), elle est visible un instant au mauvais endroit."""
    available = screen.availableGeometry()
    window.resize(min(1260, available.width() - 80), min(960, available.height() - 80))
    window.winId()
    frame = window.frameGeometry()
    frame.moveCenter(available.center())
    window.move(frame.topLeft())


def main():
    if "--splash" in sys.argv:
        from rechelper.splash import run_splash

        sys.exit(run_splash())

    # Shipped inside the same exe as the app itself — the installer's "Uninstall"
    # shortcut launches `RecSizeHelper.exe --uninstall` instead of a separate
    # uninstall.exe, so the installer doesn't need to embed a second Qt runtime.
    if "--uninstall" in sys.argv:
        from rechelper.uninstall_window import run_uninstall

        run_uninstall()
        return

    _mark("python_start")
    # Lancé avant tout le reste, même avant Qt : chaque milliseconde gagnée ici est une
    # milliseconde d'écran vide en moins.
    splash = _Splash()

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFont, QFontDatabase, QFontMetrics, QIcon
    from PySide6.QtWidgets import QApplication

    from rechelper.resources import ICON_PATH

    app = QApplication(sys.argv)
    _mark("qapp_created")
    splash.progress(10)
    app.setWindowIcon(QIcon(ICON_PATH))

    # Le premier rendu de texte d'un processus paie la base de polices Windows (~0,5 s
    # avec des centaines de familles installées) puis la police emoji (~1 s) — un coût
    # unique qui gèle le thread. Le déclencher ici, explicitement, permet à la barre du
    # splash d'avancer sur ces vraies étapes au lieu de rester figée pendant 1,5 s.
    QFontDatabase.families()
    _mark("fonts_ready")
    splash.progress(42)
    QFontMetrics(QFont("Segoe UI", 13)).horizontalAdvance(_UI_EMOJI)
    _mark("emoji_ready")
    splash.progress(74)

    from rechelper.main_window import MainWindow

    _mark("main_window_imported")
    splash.progress(82)

    window = MainWindow()
    _place_window(window, app.primaryScreen())
    _mark("window_built")
    splash.progress(93)

    window.show()
    app.processEvents()
    _mark("window_shown")
    splash.progress(100)
    splash.done()

    # Réseau seulement une fois la fenêtre à l'écran : la vérification de mise à jour
    # n'a rien à faire dans le chemin critique du lancement.
    QTimer.singleShot(1500, window.check_for_updates)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
