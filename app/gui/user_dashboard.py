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
    QHBoxLayout,
    QComboBox,
)


class UserDashboard(QWidget):
    refresh_requested = Signal()
    status_update_requested = Signal(int, str)

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

        status_layout = QHBoxLayout()

        status_label = QLabel("New Status:")
        status_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItem("To Do", "to_do")
        self.status_combo.addItem(
            "In Progress", "in_progress"
        )
        self.status_combo.addItem(
            "Completed", "completed"
        )
        status_layout.addWidget(self.status_combo)

        self.update_status_button = QPushButton(
            "Update Status"
        )
        status_layout.addWidget(
            self.update_status_button
        )

        layout.addLayout(status_layout)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

        self.update_status_button.clicked.connect(
            self._request_status_update
        )

        self.task_table.itemSelectionChanged.connect(
            self._sync_selected_status
        )


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

    def _sync_selected_status(self):
        """Match the dropdown to the selected task."""

        row = self.task_table.currentRow()

        if row < 0:
            return

        status_item = self.task_table.item(row, 2)

        if status_item is None:
            return

        index = self.status_combo.findData(
            status_item.text()
        )

        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    def _request_status_update(self):
        """Request a status change for the selected task."""

        task_id = self.selected_task_id()

        if task_id is None:
            self.error_label.setText(
                "Please select a task."
            )
            return

        new_status = self.status_combo.currentData()

        self.error_label.clear()

        self.status_update_requested.emit(
            task_id, new_status
        )


