"""
tests.py
--------
Unit tests for the StudentManagement class.
Run with:  python tests.py
"""

import os
import json
import unittest
import tempfile

from student import Student, StudentManagement


class TestStudentModel(unittest.TestCase):
    """Tests for the Student data model."""

    def test_to_dict_and_back(self):
        """Round-trip: Student → dict → Student should yield equal data."""
        s = Student("STU001", "Alice Smith", 20, "Computer Science", "alice@test.com")
        d = s.to_dict()
        s2 = Student.from_dict(d)
        self.assertEqual(s.student_id, s2.student_id)
        self.assertEqual(s.name,       s2.name)
        self.assertEqual(s.age,        s2.age)

    def test_id_uppercased(self):
        s = Student("stu99", "Bob", 18, "Math", "bob@test.com")
        self.assertEqual(s.student_id, "STU99")

    def test_name_title_cased(self):
        s = Student("X01", "john doe", 25, "Physics", "j@test.com")
        self.assertEqual(s.name, "John Doe")

    def test_email_lowercased(self):
        s = Student("X02", "Jane", 19, "Bio", "Jane@TEST.COM")
        self.assertEqual(s.email, "jane@test.com")


class TestStudentManagement(unittest.TestCase):
    """Integration tests for the StudentManagement CRUD layer."""

    def setUp(self):
        """Create a fresh temp JSON file for each test."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.mgmt = StudentManagement(db_path=self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    # ── Add ────────────────────────────────────

    def test_add_valid_student(self):
        ok, msg = self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        self.assertTrue(ok)
        self.assertEqual(self.mgmt.total_students(), 1)

    def test_add_duplicate_id(self):
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        ok, _ = self.mgmt.add_student("STU001","Bob",21,"IT","bob@x.com")
        self.assertFalse(ok)

    def test_add_invalid_email(self):
        ok, _ = self.mgmt.add_student("STU002","Carol",22,"CS","not-an-email")
        self.assertFalse(ok)

    def test_add_invalid_age_string(self):
        ok, _ = self.mgmt.add_student("STU003","Dave","abc","CS","d@x.com")
        self.assertFalse(ok)

    def test_add_age_out_of_range(self):
        ok, _ = self.mgmt.add_student("STU004","Eve",5,"CS","e@x.com")
        self.assertFalse(ok)

    def test_add_invalid_id_too_short(self):
        ok, _ = self.mgmt.add_student("AB","Eve",20,"CS","e@x.com")
        self.assertFalse(ok)

    # ── Search ─────────────────────────────────

    def test_search_existing(self):
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        s = self.mgmt.search_student("stu001")   # case-insensitive
        self.assertIsNotNone(s)
        self.assertEqual(s.name, "Alice")

    def test_search_missing(self):
        result = self.mgmt.search_student("NONE99")
        self.assertIsNone(result)

    # ── Update ─────────────────────────────────

    def test_update_name(self):
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        ok, _ = self.mgmt.update_student("STU001", name="Alicia")
        self.assertTrue(ok)
        self.assertEqual(self.mgmt.search_student("STU001").name, "Alicia")

    def test_update_email_invalid(self):
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        ok, _ = self.mgmt.update_student("STU001", email="bad-email")
        self.assertFalse(ok)

    def test_update_missing_student(self):
        ok, _ = self.mgmt.update_student("GHOST", name="Ghost")
        self.assertFalse(ok)

    def test_update_no_fields(self):
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        ok, _ = self.mgmt.update_student("STU001")   # nothing passed
        self.assertFalse(ok)

    # ── Delete ─────────────────────────────────

    def test_delete_existing(self):
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        ok, _ = self.mgmt.delete_student("STU001")
        self.assertTrue(ok)
        self.assertEqual(self.mgmt.total_students(), 0)

    def test_delete_missing(self):
        ok, _ = self.mgmt.delete_student("NONE")
        self.assertFalse(ok)

    # ── Persistence ────────────────────────────

    def test_data_persists_across_instances(self):
        """Records saved by one instance should be readable by a new instance."""
        self.mgmt.add_student("STU001","Alice",20,"CS","alice@x.com")
        mgmt2 = StudentManagement(db_path=self.tmp.name)
        self.assertEqual(mgmt2.total_students(), 1)
        self.assertIsNotNone(mgmt2.search_student("STU001"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
