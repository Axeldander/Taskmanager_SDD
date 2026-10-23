
import statistics
import tempfile
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.gui.app_controller import AppController
from app.models.task import Task


TASK_COUNT = 1000
RUNS = 5


def main():
    app = QApplication.instance() or QApplication([])

    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "benchmark.db"
        database_url = f"sqlite:///{database_path.as_posix()}"

        controller = AppController(database_url=database_url)

        controller.setup_service.create_initial_admin(
            "benchmark_admin",
            "BenchmarkPassword123!",
        )

        controller.auth_service.login(
            "benchmark_admin",
            "BenchmarkPassword123!",
        )

        user_id = controller.user_management_service.create_user(
            "benchmark_user",
            "BenchmarkUserPassword123!",
        )

        # Insert test data directly to avoid including task creation
        # time in the dashboard-loading measurement.
        with controller.session_factory() as session:
            session.add_all(
                [
                    Task(
                        title=f"Benchmark task {number}",
                        description=f"Description for task {number}",
                        assigned_user_id=user_id,
                        status="to_do",
                    )
                    for number in range(1, TASK_COUNT + 1)
                ]
            )
            session.commit()

        # Measure the initial dashboard opening with 1,000 tasks.
        start = time.perf_counter()

        controller._show_admin_dashboard()
        app.processEvents()

        initial_load_time = time.perf_counter() - start

        dashboard = controller.current_window

        print(f"Initial dashboard load: {initial_load_time:.4f} seconds")

        if initial_load_time <= 2.0:
            print("INITIAL LOAD RESULT: PASS")
        else:
            print("INITIAL LOAD RESULT: FAIL")

        print()

        if dashboard.task_table.rowCount() != TASK_COUNT:
            raise AssertionError(
                f"Expected {TASK_COUNT} tasks, found "
                f"{dashboard.task_table.rowCount()}"
            )

        # Measure the same refresh operation five times.
        timings = []

        for run_number in range(1, RUNS + 1):
            start = time.perf_counter()

            controller._refresh_admin_dashboard()
            app.processEvents()

            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            print(f"Run {run_number}: {elapsed:.4f} seconds")

        print()
        print(f"Tasks: {TASK_COUNT}")
        print(f"Average: {statistics.mean(timings):.4f} seconds")
        print(f"Maximum: {max(timings):.4f} seconds")

        if max(timings) <= 2.0:
            print("NFR-01 RESULT: PASS")
        else:
            print("NFR-01 RESULT: FAIL")

        controller.shutdown()


if __name__ == "__main__":
    main()
