import sys
from PyQt6.QtWidgets import QApplication
from ui import NeurobackApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NeurobackApp()
    window.show()
    sys.exit(app.exec())
