
from PySide6.QtCore import QDate
from app.gui.task_dialog import TaskDialog


def test_create_dialog_has_required_fields(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Create Task"
    assert dialog.title_input is not None
    assert dialog.description_input is not None
    assert dialog.assigned_user_combo is not None
    assert dialog.deadline_checkbox is not None
    assert dialog.deadline_input is not None
    assert dialog.save_button.text() == "Save"
    assert dialog.cancel_button.text() == "Cancel"


def test_dialog_populates_available_users(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.set_users([
        (2, "alice"),
        (3, "bob"),
    ])

    assert dialog.assigned_user_combo.count() == 2
    assert dialog.assigned_user_combo.itemText(0) == "alice"
    assert dialog.assigned_user_combo.itemData(0) == 2
    assert dialog.assigned_user_combo.itemText(1) == "bob"


def test_dialog_rejects_empty_title(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.set_users([(2, "alice")])
    dialog.title_input.setText("   ")
    dialog.save_button.click()

    assert dialog.error_label.text() == "Task title cannot be empty."


def test_dialog_rejects_title_over_200_characters(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.set_users([(2, "alice")])
    dialog.title_input.setText("A" * 201)
    dialog.save_button.click()

    assert "200 characters" in dialog.error_label.text()


def test_dialog_rejects_missing_assignee(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.title_input.setText("Prepare report")
    dialog.description_input.setPlainText(
        "Prepare the coursework report"
    )
    dialog.save_button.click()

    assert dialog.error_label.text() == "Select a user."


def test_create_dialog_emits_task_data(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.set_users([(2, "alice"), (3, "bob")])
    dialog.title_input.setText("Prepare report")
    dialog.description_input.setPlainText("Finish by Friday")
    dialog.assigned_user_combo.setCurrentIndex(1)

    with qtbot.waitSignal(
        dialog.task_saved, timeout=1000
    ) as blocker:
        dialog.save_button.click()

    data = blocker.args[0]

    assert data["title"] == "Prepare report"
    assert data["description"] == "Finish by Friday"
    assert data["assigned_user_id"] == 3
    assert data["deadline"] is None


def test_edit_dialog_loads_existing_task(qtbot):
    dialog = TaskDialog(task_id=15)
    qtbot.addWidget(dialog)

    dialog.set_users([(2, "alice"), (3, "bob")])

    dialog.load_task({
        "id": 15,
        "title": "Original title",
        "description": "Original description",
        "assigned_user_id": 3,
        "deadline": None,
    })

    assert dialog.windowTitle() == "Edit Task"
    assert dialog.title_input.text() == "Original title"
    assert (
        dialog.description_input.toPlainText()
        == "Original description"
    )
    assert dialog.assigned_user_combo.currentData() == 3


def test_dialog_emits_optional_deadline(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.set_users([(2, "alice")])
    dialog.title_input.setText("Deadline task")
    dialog.description_input.setPlainText(
        "Complete the task before the deadline"
    )
    dialog.deadline_checkbox.setChecked(True)
    dialog.deadline_input.setDate(QDate(2026, 12, 15))

    with qtbot.waitSignal(
        dialog.task_saved, timeout=1000
    ) as blocker:
        dialog.save_button.click()

    assert blocker.args[0]["deadline"] == "2026-12-15"


def test_cancel_rejects_dialog(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    with qtbot.waitSignal(
        dialog.rejected, timeout=1000
    ):
        dialog.cancel_button.click()


def test_task_dialog_rejects_empty_description(qtbot):
    dialog = TaskDialog()
    qtbot.addWidget(dialog)

    dialog.set_users([(1, "alice")])
    dialog.title_input.setText("Prepare report")
    dialog.description_input.setPlainText("   ")

    emitted_tasks = []
    dialog.task_saved.connect(emitted_tasks.append)

    dialog.save_button.click()

    assert dialog.error_label.text() == (
        "Task description cannot be empty."
    )
    assert emitted_tasks == []
