import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from rechelper.main_window import MainWindow
from rechelper.resources import ICON_PATH


def main():
    # Shipped inside the same exe as the app itself — the installer's "Uninstall"
    # shortcut launches `RecSizeHelper.exe --uninstall` instead of a separate
    # uninstall.exe, so the installer doesn't need to embed a second Qt runtime.
    if "--uninstall" in sys.argv:
        from rechelper.uninstall_window import run_uninstall
        run_uninstall()
        return

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))
    window = MainWindow()
    window.resize(1260, 960)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
