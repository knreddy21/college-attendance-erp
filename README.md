# College Attendance & Marks Management System (Django + MySQL)

This is a web-based conversion of the uploaded console Student Management System. It retains the original student ID/name/course/email concepts and adds student profiles, departments, faculty, subjects, attendance, marks, reports and Excel exports.

## 1. Requirements
- Python 3.10+
- MySQL 8+
- MySQL development/build tools required by `mysqlclient` on Windows

## 2. Setup (Windows PowerShell)
```powershell
cd college_attendance_erp
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and a strong `SECRET_KEY`.

Create the database in MySQL:
```sql
CREATE DATABASE college_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. Initialize and run
```powershell
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/ and sign in. Use `/admin/` to configure departments, semesters, academic years, faculty, subjects, examinations, grading rules and users.

If no `DB_NAME` is set in `.env`, the project uses SQLite for quick local evaluation. To use MySQL, set `DB_NAME` and the other DB variables before running migrations.

## 4. Import the original JSON student records
Copy the original `students.json` file from the uploaded project into this folder, then run:
```powershell
python manage.py import_legacy_students --file students.json
```
The import maps `student_id` to both Student ID and Roll Number, and preserves name, course and email. Existing IDs are skipped. The original JSON file is not deleted or modified.

## 5. Main URLs
- `/` Dashboard
- `/students/` Student list
- `/students/add/` Add student
- `/attendance/` Attendance records
- `/attendance/mark/` Mark/update one attendance record
- `/attendance/reports/` Attendance percentage report
- `/marks/` Marks records
- `/marks/add/` Enter marks
- `/admin/` Master data and configuration
- `/exports/students.xlsx` Student Excel
- `/exports/attendance.xlsx` Attendance Excel
- `/exports/marks.xlsx` Marks Excel

## 6. Important implementation notes
- Login is required for application pages and exports.
- Django admin users manage master data. Create a staff/superuser account for initial setup.
- Attendance uniqueness is enforced per student + subject + date.
- The attendance report groups by student and subject over the selected date range.
- Attendance percentage currently treats only Present as attended; On Duty is separately counted. Align OD treatment with your institution policy before production.
- Grade rules are configurable through Django admin (`GradingRule`). Add the college's official grading bands before relying on result status.
- The dashboard's shortage list is based on each student's overall attendance records. For official subject-wise shortage notices, use the attendance reports.
- This is a starter implementation. Before public deployment, set `DEBUG=False`, configure `ALLOWED_HOSTS`, HTTPS, secure cookies, backups, and production static/media storage.

## 7. Existing console source
The original `main.py`, `student.py`, `display.py`, `tests.py`, `students.json` and README are retained in `legacy_console/` in the delivered ZIP for reference.
