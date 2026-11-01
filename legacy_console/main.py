"""
main.py
-------
Entry point for the Student Management System.
Drives the interactive menu loop, delegating work to StudentManagement
and using display helpers for all console output.

Run:
    python main.py
"""

import os
import sys

from student  import StudentManagement
from display  import (
    print_banner, print_menu, success, error, info,
    print_student_table, print_student_card,
    prompt, section_title, pause, c, Colour,
)


# ── Path of the persistent JSON data file ─────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "students.json")


# ── Action handlers ────────────────────────────────────────────────────────────

def handle_add(mgmt: StudentManagement):
    """Collect new-student details from the user and call mgmt.add_student()."""
    section_title("ADD  NEW  STUDENT")

    student_id = prompt("Student ID  (e.g. STU007)")
    name       = prompt("Full Name")
    age        = prompt("Age")
    course     = prompt("Course / Programme")
    email      = prompt("Email Address")

    ok, msg = mgmt.add_student(student_id, name, age, course, email)
    (success if ok else error)(msg)


def handle_view(mgmt: StudentManagement):
    """Display all students in a formatted table."""
    section_title("ALL  STUDENTS")
    students = mgmt.get_all_students()
    print_student_table(students)


def handle_search(mgmt: StudentManagement):
    """Search for a student by ID and display a detail card if found."""
    section_title("SEARCH  STUDENT")

    student_id = prompt("Enter Student ID to search")
    student    = mgmt.search_student(student_id)

    if student:
        print_student_card(student)
    else:
        error(f"No student found with ID '{student_id.upper()}'.")


def handle_update(mgmt: StudentManagement):
    """
    Allow the user to update any combination of fields for an existing student.
    Fields left blank are left unchanged.
    """
    section_title("UPDATE  STUDENT  DETAILS")

    student_id = prompt("Enter Student ID to update")

    # Confirm the record exists before asking for new values.
    if not mgmt.search_student(student_id):
        error(f"No student found with ID '{student_id.upper()}'.")
        return

    info("Leave a field blank to keep the current value.")

    name   = prompt("New Name",    optional=True)
    age    = prompt("New Age",     optional=True)
    course = prompt("New Course",  optional=True)
    email  = prompt("New Email",   optional=True)

    ok, msg = mgmt.update_student(
        student_id, name=name, age=age, course=course, email=email
    )
    (success if ok else error)(msg)


def handle_delete(mgmt: StudentManagement):
    """Ask for an ID, show the student's details, confirm, then delete."""
    section_title("DELETE  STUDENT")

    student_id = prompt("Enter Student ID to delete")
    student    = mgmt.search_student(student_id)

    if not student:
        error(f"No student found with ID '{student_id.upper()}'.")
        return

    # Show a preview before asking for confirmation.
    print_student_card(student)

    confirm = prompt(
        c(f"Are you sure you want to delete '{student.name}'? (yes / no)", Colour.RED)
    ).lower()

    if confirm in ("yes", "y"):
        ok, msg = mgmt.delete_student(student_id)
        (success if ok else error)(msg)
    else:
        info("Delete cancelled — no changes were made.")


# ── Menu dispatcher ────────────────────────────────────────────────────────────

ACTIONS = {
    "1": handle_add,
    "2": handle_view,
    "3": handle_search,
    "4": handle_update,
    "5": handle_delete,
}


def main():
    # Ensure the data directory exists (the JSON file lives here).
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # Initialise the management system (loads existing data from JSON).
    mgmt = StudentManagement(db_path=DATA_FILE)

    # Welcome screen
    os.system("cls" if os.name == "nt" else "clear")
    print_banner()
    info(f"Data file: {DATA_FILE}  |  Students loaded: {mgmt.total_students()}")

    # ── Main loop ──────────────────────────────────────────────────────────────
    while True:
        print_menu()

        choice = prompt("Enter your choice (1–6)").strip()

        if choice == "6":
            print(c("\n  Goodbye! See you next time. 👋\n", Colour.GREEN))
            sys.exit(0)

        action = ACTIONS.get(choice)
        if action:
            action(mgmt)
        else:
            error("Invalid choice. Please enter a number from 1 to 6.")

        pause()


# ── Script entry ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
