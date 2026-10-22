
import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from app.database.connection import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)


def main():
    engine = create_database_engine()
    initialize_database(engine)

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Desktop Task Manager")
    window.resize(900, 600)

    label = QLabel("Task Manager - SDD Prototype")
    label.setStyleSheet("font-size: 24px; padding: 30px;")
    window.setCentralWidget(label)

    window.show()

    exit_code = app.exec()

    engine.dispose()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
