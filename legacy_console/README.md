# 🎓 Student Management System

A complete, menu-driven **Student Management System** written in pure Python.  
It supports full **CRUD** operations, persists data in a **JSON** file, validates all user input, and follows **OOP principles** throughout.

---

## 📁 Project Structure

```
student_management_system/
├── main.py            # Entry point — menu loop & action handlers
├── student.py         # Student model + StudentManagement class (OOP core)
├── display.py         # Console UI helpers (tables, cards, colours, prompts)
├── tests.py           # Unit & integration tests (unittest)
├── data/
│   └── students.json  # Persistent data store (auto-created on first run)
└── README.md          # This file
```

---

## ✨ Features

| # | Feature | Details |
|---|---------|---------|
| 1 | **Add Student** | ID, Name, Age, Course, Email — all validated |
| 2 | **View All Students** | Colour-coded, formatted table sorted by name |
| 3 | **Search by ID** | Case-insensitive lookup with a detail card |
| 4 | **Update Details** | Update any field; blank = keep current value |
| 5 | **Delete Student** | Preview + confirmation prompt before deletion |
| 6 | **Persistent Storage** | Auto-saves to `data/students.json` after every change |
| 7 | **Input Validation** | ID format, age range, e-mail regex, empty-field checks |
| 8 | **OOP Design** | `Student` model + `StudentManagement` service class |
| 9 | **Colour UI** | ANSI colours, section headers, table borders |
| 10 | **Unit Tests** | 18 tests covering all CRUD paths and edge cases |

---

## 🚀 Setup & Run

### Prerequisites
- Python **3.10+** (uses `int | None` union syntax)
- No external packages required — standard library only

### Steps

```bash
# 1. Clone or download the project folder
cd student_management_system

# 2. (Optional) load sample data
#    The data/students.json file ships with 10 sample records.
#    If you delete it, the system starts fresh automatically.

# 3. Run the application
python main.py

# 4. Run the test suite
python tests.py
```

---

## 🖥️ Usage Guide

```
  MAIN MENU
  ─────────────────────────────────────
  1. Add Student         ← enter new record
  2. View All Students   ← formatted table
  3. Search Student      ← lookup by ID
  4. Update Details      ← edit any field
  5. Delete Student      ← with confirmation
  6. Exit
```

### Student ID rules
- 3–12 alphanumeric characters (letters + digits only)
- Automatically uppercased
- Must be unique — duplicates are rejected
- Examples: `STU001`, `S42`, `ENG2024A`

### Age rules
- Must be a whole number between **10** and **100**

### Email rules
- Standard format: `user@domain.tld`

---

## 🧪 Running Tests

```bash
python tests.py -v
```

Expected output (all 18 tests):

```
test_add_age_out_of_range ... ok
test_add_duplicate_id ...     ok
test_add_invalid_age_string ...ok
test_add_invalid_email ...    ok
test_add_invalid_id_too_short ok
test_add_valid_student ...    ok
test_data_persists_across_instances ok
test_delete_existing ...      ok
test_delete_missing ...       ok
test_email_lowercased ...     ok
test_id_uppercased ...        ok
test_name_title_cased ...     ok
test_search_existing ...      ok
test_search_missing ...       ok
test_to_dict_and_back ...     ok
test_update_email_invalid ... ok
test_update_missing_student ...ok
test_update_name ...          ok
test_update_no_fields ...     ok
----------------------------------------------------------------------
Ran 19 tests in 0.XXXs — OK
```

---

## 🗃️ Sample Data

`data/students.json` ships with **10 sample records** (IDs STU001–STU010) covering a variety of courses so you can explore all features immediately.

---

## 🏗️ Architecture

```
main.py  (UI / controller)
   │
   ├── StudentManagement  (service layer)  ← student.py
   │       │
   │       └── Student  (data model)       ← student.py
   │
   └── display.py  (presentation layer)
```

The three-layer architecture separates **presentation**, **business logic**, and **data** concerns, making each component independently testable and easy to extend.

---

## 🔮 Future Enhancements

- **SQLite / PostgreSQL** backend instead of JSON
- **REST API** wrapper (FastAPI) to serve data over HTTP
- **CSV / Excel export** of student records
- **Role-based access control** (admin vs. read-only users)
- **Pagination** for large datasets
- **Search by name or course**, not just ID
- **Web / GUI front-end** (Tkinter, Flask, or React)
- **Bulk import** from CSV

---

## 📝 License

MIT — free to use, modify, and distribute.
