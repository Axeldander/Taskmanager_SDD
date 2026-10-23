
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)


class UserDashboard(QWidget):
    refresh_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager - My Tasks")
        self.setMinimumSize(750, 450)

        layout = QVBoxLayout(self)

        heading = QLabel("My Assigned Tasks")
        heading.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(heading)

        description = QLabel(
            "View the tasks assigned to your account."
        )
        layout.addWidget(description)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )
        layout.addWidget(self.refresh_button)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Title",
                "Status",
                "Deadline",
            ]
        )

        self.task_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.task_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.task_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.task_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.task_table)

    def display_tasks(self, tasks):
        """Display tasks assigned to the logged-in user."""
        self.task_table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            deadline = task.get("deadline")

            values = [
                str(task["id"]),
                task["title"],
                task["status"],
                str(deadline) if deadline is not None else "",
            ]

            for column, value in enumerate(values):
                self.task_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

    def selected_task_id(self):
        """Return the ID of the selected task, if any."""
        row = self.task_table.currentRow()

        if row < 0:
            return None

        item = self.task_table.item(row, 0)

        if item is None:
            return None

        return int(item.text())
