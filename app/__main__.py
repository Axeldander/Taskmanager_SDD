import sys

from PySide6.QtWidgets import QApplication

from app.gui.app_controller import AppController


def main():
    application = QApplication(sys.argv)

    controller = AppController()
    controller.start()

    exit_code = application.exec()

    controller.shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())