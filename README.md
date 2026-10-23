# Desktop Task Management System

A Python desktop task manager developed using a Specification-Driven Development (SDD) approach for a university project comparing SDD with Vibe Coding.

The application runs locally on Windows and allows administrators to assign tasks to standard users and monitor their progress.

## Features

**Administrator**
- Set up the first administrator account on initial launch.
- Create standard-user accounts.
- Create tasks with titles, descriptions, and optional deadlines.
- Assign and reassign tasks to users.
- Edit and delete tasks.
- Monitor task statuses and assigned users.

**Standard user**
- Log in securely.
- View only assigned tasks.
- View task descriptions, deadlines, and statuses.
- Update task status to To Do, In Progress, or Completed.

**Additional features**
- Password hashing using Argon2.
- Local SQLite database with persistent storage.
- Role-based access control.
- Offline operation.

## Technology Stack

- Python 3.11.5
- PySide6
- SQLAlchemy
- SQLite
- argon2-cffi
- pytest and pytest-qt
- GitHub Spec Kit-style SDD documentation

## Requirements

- Windows 10 or a compatible Windows environment
- Python 3.11
- Internet connection for initial dependency installation

## Installation

Clone the repository and open the project folder:

```powershell
git clone <REPOSITORY_URL>
cd <REPOSITORY_FOLDER>
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
pip install PySide6-Essentials SQLAlchemy argon2-cffi pytest pytest-qt
```

## Running the Application

From the project root, run:

```powershell
python -m app
```

On the first launch, create the administrator account using a password containing at least 12 characters.

After setup, log in as the administrator to create standard users and assign tasks.

Application data is stored locally in a SQLite database.

## Running Tests

Run the full automated test suite:

```powershell
python -m pytest -q
```

**Latest verification result:** 128 tests passed.

Run the 1,000-task dashboard performance benchmark:

```powershell
python -m tests.benchmark_dashboard
```

The measured initial dashboard load was 0.2431 seconds, below the two-second requirement.

## Specification-Driven Development

The project follows a specification-driven workflow using the following documents:

- `specs/001-task-management/spec.md` — requirements and acceptance criteria.
- `specs/001-task-management/plan.md` — technical implementation plan.
- `specs/001-task-management/tasks.md` — implementation and verification checklist.
- `specs/001-task-management/verification-report.md` — testing results and audit evidence.

## Project Scope

This version is designed for offline use on a single Windows computer.

It does not include network synchronization, mobile applications, notifications, or self-registration.

## Academic Context

This application was created as the SDD implementation for a university assignment comparing Specification-Driven Development and Vibe Coding.