import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui import IniEditor
from utils import resource_path


def main():
    app = QApplication(sys.argv)
    editor = IniEditor()
    editor.setWindowIcon(QIcon(resource_path('assets/Rainmeter_Editor.png')))
    editor.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
