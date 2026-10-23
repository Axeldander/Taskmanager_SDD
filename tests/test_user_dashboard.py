
from app.gui.user_dashboard import UserDashboard


def test_user_dashboard_has_required_controls(qtbot):
    window = UserDashboard()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Task Manager - My Tasks"
    assert window.task_table.columnCount() == 4
    assert window.refresh_button.text() == "Refresh"


def test_user_dashboard_displays_assigned_tasks(qtbot):
    window = UserDashboard()
    qtbot.addWidget(window)

    tasks = [
        {
            "id": 1,
            "title": "Prepare report",
            "status": "to_do",
            "deadline": None,
        },
        {
            "id": 2,
            "title": "Review documents",
            "status": "in_progress",
            "deadline": "2026-12-15",
        },
    ]

    window.display_tasks(tasks)

    assert window.task_table.rowCount() == 2
    assert window.task_table.item(0, 1).text() == "Prepare report"
    assert window.task_table.item(1, 2).text() == "in_progress"
    assert window.task_table.item(1, 3).text() == "2026-12-15"


def test_user_dashboard_has_no_admin_controls(qtbot):
    window = UserDashboard()
    qtbot.addWidget(window)

    assert not hasattr(window, "create_user_button")
    assert not hasattr(window, "create_task_button")
    assert not hasattr(window, "edit_task_button")
    assert not hasattr(window, "delete_task_button")


def test_user_dashboard_refresh_signal(qtbot):
    window = UserDashboard()
    qtbot.addWidget(window)

    with qtbot.waitSignal(
        window.refresh_requested, timeout=1000
    ):
        window.refresh_button.click()
