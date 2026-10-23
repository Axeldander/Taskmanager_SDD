
from app.gui.admin_dashboard import AdminDashboard


def test_admin_dashboard_has_required_controls(qtbot):
    window = AdminDashboard()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Task Manager - Administrator"
    assert window.task_table.columnCount() == 5
    assert window.create_user_button.text() == "Create User"
    assert window.create_task_button.text() == "Create Task"
    assert window.edit_task_button.text() == "Edit Task"
    assert window.delete_task_button.text() == "Delete Task"
    assert window.refresh_button.text() == "Refresh"


def test_admin_dashboard_displays_tasks(qtbot):
    window = AdminDashboard()
    qtbot.addWidget(window)

    tasks = [
        {
            "id": 1,
            "title": "Prepare report",
            "status": "to_do",
            "assigned_user": "alice",
            "deadline": None,
        },
        {
            "id": 2,
            "title": "Review project",
            "status": "completed",
            "assigned_user": "bob",
            "deadline": None,
        },
    ]

    window.display_tasks(tasks)

    assert window.task_table.rowCount() == 2
    assert window.task_table.item(0, 1).text() == "Prepare report"
    assert window.task_table.item(1, 2).text() == "completed"


def test_admin_dashboard_displays_status_summary(qtbot):
    window = AdminDashboard()
    qtbot.addWidget(window)

    window.display_status_summary(
        {
            "to_do": 3,
            "in_progress": 2,
            "completed": 5,
        }
    )

    assert window.todo_count.text() == "To Do: 3"
    assert window.progress_count.text() == "In Progress: 2"
    assert window.completed_count.text() == "Completed: 5"
