
from PySide6.QtCore import Signal, QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QPushButton,
)


class TaskDialog(QDialog):
    task_saved = Signal(dict)

    def __init__(self, task_id=None, parent=None):
        super().__init__(parent)

        self.task_id = task_id

        if task_id is None:
            self.setWindowTitle("Create Task")
        else:
            self.setWindowTitle("Edit Task")

        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task title")
        form.addRow("Title:", self.title_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Task description"
        )
        self.description_input.setMaximumHeight(120)
        form.addRow(
            "Description:", self.description_input
        )

        self.assigned_user_combo = QComboBox()
        form.addRow(
            "Assigned User:", self.assigned_user_combo
        )

        self.deadline_checkbox = QCheckBox(
            "Set deadline"
        )
        form.addRow("", self.deadline_checkbox)

        self.deadline_input = QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDate(
            QDate.currentDate()
        )
        self.deadline_input.setEnabled(False)
        form.addRow("Deadline:", self.deadline_input)

        self.deadline_checkbox.toggled.connect(
            self.deadline_input.setEnabled
        )

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            "color: red;"
        )
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(buttons)

        self.save_button.clicked.connect(
            self._handle_save
        )
        self.cancel_button.clicked.connect(
            self.reject
        )

    def set_users(self, users):
        """Populate the list of standard users.

        users: list of (user_id, username) tuples
        """
        self.assigned_user_combo.clear()

        for user_id, username in users:
            self.assigned_user_combo.addItem(
                username, user_id
            )

    def load_task(self, task):
        """Populate fields with an existing task."""
        self.task_id = task["id"]
        self.setWindowTitle("Edit Task")

        self.title_input.setText(
            task["title"]
        )
        self.description_input.setPlainText(
            task["description"]
        )

        index = self.assigned_user_combo.findData(
            task["assigned_user_id"]
        )

        if index >= 0:
            self.assigned_user_combo.setCurrentIndex(
                index
            )
        else:
            self.assigned_user_combo.setCurrentIndex(-1)

        deadline = task.get("deadline")

        if deadline:
            if isinstance(deadline, str):
                date = QDate.fromString(
                    deadline[:10],
                    "yyyy-MM-dd",
                )
            else:
                date = QDate(
                    deadline.year,
                    deadline.month,
                    deadline.day,
                )

            if date.isValid():
                self.deadline_input.setDate(date)
                self.deadline_checkbox.setChecked(True)
            else:
                self.deadline_checkbox.setChecked(False)
        else:
            self.deadline_checkbox.setChecked(False)

    def _handle_save(self):
        title = self.title_input.text().strip()
        description = (
            self.description_input.toPlainText()
        )
        assigned_user_id = (
            self.assigned_user_combo.currentData()
        )

        if not title:
            self.error_label.setText(
                "Task title cannot be empty."
            )
            return

        if len(title) > 200:
            self.error_label.setText(
                "Task title cannot exceed 200 characters."
            )
            return

        if assigned_user_id is None:
            self.error_label.setText(
                "Select a user."
            )
            return

        deadline = None

        if self.deadline_checkbox.isChecked():
            deadline = (
                self.deadline_input.date()
                .toString("yyyy-MM-dd")
            )

        self.error_label.clear()

        data = {
            "title": title,
            "description": description,
            "assigned_user_id": assigned_user_id,
            "deadline": deadline,
        }

        self.task_saved.emit(data)

    def show_error(self, message):
        self.error_label.setText(message)
