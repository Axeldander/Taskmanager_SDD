
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)


class AdminDashboard(QWidget):
    create_user_requested = Signal()
    create_task_requested = Signal()
    edit_task_requested = Signal(int)
    delete_task_requested = Signal(int)
    refresh_requested = Signal()
    logout_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager - Administrator")
        self.setMinimumSize(900, 550)

        layout = QVBoxLayout(self)

        heading = QLabel("Administrator Dashboard")
        heading.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(heading)

        summary_layout = QHBoxLayout()

        self.todo_count = QLabel("To Do: 0")
        self.progress_count = QLabel("In Progress: 0")
        self.completed_count = QLabel("Completed: 0")

        summary_layout.addWidget(self.todo_count)
        summary_layout.addWidget(self.progress_count)
        summary_layout.addWidget(self.completed_count)

        layout.addLayout(summary_layout)

        button_layout = QHBoxLayout()

        self.create_user_button = QPushButton("Create User")
        self.create_task_button = QPushButton("Create Task")
        self.edit_task_button = QPushButton("Edit Task")
        self.delete_task_button = QPushButton("Delete Task")
        self.refresh_button = QPushButton("Refresh")
        self.logout_button = QPushButton("Log Out")


        button_layout.addWidget(self.create_user_button)
        button_layout.addWidget(self.create_task_button)
        button_layout.addWidget(self.edit_task_button)
        button_layout.addWidget(self.delete_task_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.logout_button)

        layout.addLayout(button_layout)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Title",
                "Status",
                "Assigned User",
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

        self.create_user_button.clicked.connect(
            self.create_user_requested.emit
        )
        self.create_task_button.clicked.connect(
            self.create_task_requested.emit
        )
        self.edit_task_button.clicked.connect(
            self._request_edit
        )
        self.delete_task_button.clicked.connect(
            self._request_delete
        )
        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )
        self.logout_button.clicked.connect(
            self.logout_requested.emit
        )

    def selected_task_id(self):
        row = self.task_table.currentRow()

        if row < 0:
            return None

        item = self.task_table.item(row, 0)

        if item is None:
            return None

        return int(item.text())

    def _request_edit(self):
        task_id = self.selected_task_id()

        if task_id is not None:
            self.edit_task_requested.emit(task_id)

    def _request_delete(self):
        task_id = self.selected_task_id()

        if task_id is not None:
            self.delete_task_requested.emit(task_id)

    def display_tasks(self, tasks):
        self.task_table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            values = [
                str(task["id"]),
                task["title"],
                task["status"],
                task["assigned_user"],
                str(task["deadline"])
                if task["deadline"] is not None
                else "",
            ]

            for column, value in enumerate(values):
                self.task_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

    def display_status_summary(self, summary):
        self.todo_count.setText(
            f"To Do: {summary.get('to_do', 0)}"
        )
        self.progress_count.setText(
            f"In Progress: {summary.get('in_progress', 0)}"
        )
        self.completed_count.setText(
            f"Completed: {summary.get('completed', 0)}"
        )

