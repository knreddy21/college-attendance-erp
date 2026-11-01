"""
student.py
----------
Core module defining the Student data model and StudentManagement system.
Follows Object-Oriented Programming (OOP) principles.
"""

import json
import os
import re
from datetime import datetime


# ──────────────────────────────────────────────
# Student Model
# ──────────────────────────────────────────────

class Student:
    """
    Represents a single student record.

    Attributes:
        student_id (str): Unique identifier (e.g. "STU001").
        name       (str): Full name of the student.
        age        (int): Age of the student (must be 10–100).
        course     (str): Enrolled course / programme.
        email      (str): Contact e-mail address.
        created_at (str): ISO timestamp when the record was created.
    """

    def __init__(self, student_id: str, name: str, age: int,
                 course: str, email: str, created_at: str = None):
        self.student_id = student_id.strip().upper()
        self.name       = name.strip().title()
        self.age        = int(age)
        self.course     = course.strip().title()
        self.email      = email.strip().lower()
        # Persist creation timestamp; default to "now" for new records.
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Serialisation helpers ──────────────────

    def to_dict(self) -> dict:
        """Convert the Student object to a plain dictionary (for JSON storage)."""
        return {
            "student_id": self.student_id,
            "name":       self.name,
            "age":        self.age,
            "course":     self.course,
            "email":      self.email,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Reconstruct a Student object from a dictionary (loaded from JSON)."""
        return cls(
            student_id = data["student_id"],
            name       = data["name"],
            age        = data["age"],
            course     = data["course"],
            email      = data["email"],
            created_at = data.get("created_at"),
        )

    def __repr__(self) -> str:
        return (f"Student(id={self.student_id!r}, name={self.name!r}, "
                f"age={self.age}, course={self.course!r})")


# ──────────────────────────────────────────────
# StudentManagement System
# ──────────────────────────────────────────────

class StudentManagement:
    """
    Manages a collection of Student objects with full CRUD operations.
    Data is persisted to a JSON file so records survive between sessions.

    Args:
        db_path (str): Path to the JSON file used as the data store.
    """

    def __init__(self, db_path: str = "students.json"):
        self.db_path  = db_path
        self.students: dict[str, Student] = {}  # {student_id: Student}
        self._load()

    # ── Persistence ───────────────────────────

    def _load(self):
        """Load student records from the JSON file into memory."""
        if not os.path.exists(self.db_path):
            return  # No file yet — start with an empty store.
        try:
            with open(self.db_path, "r", encoding="utf-8") as fh:
                raw: list[dict] = json.load(fh)
            for record in raw:
                s = Student.from_dict(record)
                self.students[s.student_id] = s
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"  [Warning] Could not load data file: {exc}")

    def _save(self):
        """Persist all in-memory student records to the JSON file."""
        data = [s.to_dict() for s in self.students.values()]
        with open(self.db_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)

    # ── Validation helpers ────────────────────

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Return True if the e-mail address looks syntactically valid."""
        pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def _validate_age(age_str: str) -> tuple[bool, int]:
        """
        Attempt to parse age_str as an integer in [10, 100].
        Returns (True, age_int) on success or (False, 0) on failure.
        """
        try:
            age = int(age_str)
            return (10 <= age <= 100, age)
        except ValueError:
            return (False, 0)

    @staticmethod
    def _validate_id(sid: str) -> bool:
        """
        Student IDs must be 3–12 alphanumeric characters.
        Examples: STU001, S42, ABC123XYZ
        """
        return bool(re.match(r"^[A-Za-z0-9]{3,12}$", sid.strip()))

    # ── CRUD operations ───────────────────────

    def add_student(self, student_id: str, name: str, age_str: str,
                    course: str, email: str) -> tuple[bool, str]:
        """
        Validate inputs and add a new student record.

        Returns:
            (True,  success_message) on success.
            (False, error_message)   on validation failure or duplicate ID.
        """
        # — ID validation
        if not self._validate_id(student_id):
            return False, "Invalid ID. Use 3–12 alphanumeric characters (e.g. STU001)."

        sid = student_id.strip().upper()
        if sid in self.students:
            return False, f"Student ID '{sid}' already exists."

        # — Name validation
        name = name.strip()
        if not name or len(name) < 2:
            return False, "Name must be at least 2 characters long."

        # — Age validation
        ok, age = self._validate_age(age_str)
        if not ok:
            return False, "Age must be a whole number between 10 and 100."

        # — Course validation
        course = course.strip()
        if not course or len(course) < 2:
            return False, "Course name must be at least 2 characters long."

        # — Email validation
        if not self._validate_email(email.strip()):
            return False, "Invalid e-mail address format."

        # All checks passed — create and store the record.
        student = Student(sid, name, age, course, email)
        self.students[sid] = student
        self._save()
        return True, f"Student '{student.name}' added successfully with ID {sid}."

    def get_all_students(self) -> list[Student]:
        """Return all students sorted alphabetically by name."""
        return sorted(self.students.values(), key=lambda s: s.name)

    def search_student(self, student_id: str) -> Student | None:
        """Look up a student by ID (case-insensitive). Returns None if not found."""
        return self.students.get(student_id.strip().upper())

    def update_student(self, student_id: str, **kwargs) -> tuple[bool, str]:
        """
        Update one or more fields of an existing student record.

        Accepted keyword arguments: name, age, course, email.
        Blank values (empty strings) are treated as "no change".

        Returns:
            (True,  success_message) on success.
            (False, error_message)   if the student is not found or input is invalid.
        """
        sid = student_id.strip().upper()
        student = self.students.get(sid)
        if not student:
            return False, f"No student found with ID '{sid}'."

        updated_fields = []

        # — Name
        if kwargs.get("name", "").strip():
            name = kwargs["name"].strip()
            if len(name) < 2:
                return False, "Name must be at least 2 characters long."
            student.name = name.title()
            updated_fields.append("name")

        # — Age
        if kwargs.get("age", "").strip():
            ok, age = self._validate_age(kwargs["age"].strip())
            if not ok:
                return False, "Age must be a whole number between 10 and 100."
            student.age = age
            updated_fields.append("age")

        # — Course
        if kwargs.get("course", "").strip():
            course = kwargs["course"].strip()
            if len(course) < 2:
                return False, "Course name must be at least 2 characters long."
            student.course = course.title()
            updated_fields.append("course")

        # — Email
        if kwargs.get("email", "").strip():
            email = kwargs["email"].strip()
            if not self._validate_email(email):
                return False, "Invalid e-mail address format."
            student.email = email.lower()
            updated_fields.append("email")

        if not updated_fields:
            return False, "No changes were made (all fields left blank)."

        self._save()
        fields_str = ", ".join(updated_fields)
        return True, f"Student '{student.name}' updated successfully ({fields_str})."

    def delete_student(self, student_id: str) -> tuple[bool, str]:
        """
        Remove a student record permanently.

        Returns:
            (True,  success_message) on success.
            (False, error_message)   if the student is not found.
        """
        sid = student_id.strip().upper()
        student = self.students.pop(sid, None)
        if not student:
            return False, f"No student found with ID '{sid}'."
        self._save()
        return True, f"Student '{student.name}' (ID: {sid}) deleted successfully."

    def total_students(self) -> int:
        """Return the total number of stored students."""
        return len(self.students)
