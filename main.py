import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from rechelper.main_window import MainWindow
from rechelper.resources import ICON_PATH


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))
    window = MainWindow()
    window.resize(1260, 960)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
