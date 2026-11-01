"""
display.py
----------
Console UI helpers: banners, menus, formatted tables, and colour output.
Keeps all presentation logic separate from business logic (Single Responsibility).
"""

# ── ANSI colour codes (work on most modern terminals) ─────────────────────────

class Colour:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"


def c(text: str, colour: str) -> str:
    """Wrap *text* in an ANSI colour code."""
    return f"{colour}{text}{Colour.RESET}"


# ── Banner & menu ──────────────────────────────────────────────────────────────

BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║   ____  __  __ ____                                 ║
  ║  / ___||  \/  / ___|                                ║
  ║  \___ \| |\/| \___ \                                ║
  ║   ___) | |  | |___) |                               ║
  ║  |____/|_|  |_|____/  Student Management System     ║
  ║                                v1.0                 ║
  ╚══════════════════════════════════════════════════════╝
"""

MENU = """
  ┌──────────────────────────────────┐
  │         MAIN  MENU               │
  ├──────────────────────────────────┤
  │  1. Add Student                  │
  │  2. View All Students            │
  │  3. Search Student by ID         │
  │  4. Update Student Details       │
  │  5. Delete Student               │
  │  6. Exit                         │
  └──────────────────────────────────┘
"""


def print_banner():
    print(c(BANNER, Colour.CYAN))


def print_menu():
    print(c(MENU, Colour.WHITE))


# ── Result messages ────────────────────────────────────────────────────────────

def success(msg: str):
    print(f"\n  {c('✔', Colour.GREEN)}  {c(msg, Colour.GREEN)}\n")


def error(msg: str):
    print(f"\n  {c('✘', Colour.RED)}  {c(msg, Colour.RED)}\n")


def info(msg: str):
    print(f"\n  {c('ℹ', Colour.CYAN)}  {c(msg, Colour.CYAN)}\n")


# ── Student table ──────────────────────────────────────────────────────────────

# Column widths  (characters)
COL = {
    "id":    10,
    "name":  22,
    "age":    5,
    "course": 24,
    "email":  30,
    "created":18,
}

def _cell(text: str, width: int) -> str:
    """Left-justify and truncate text to fit a table cell."""
    text = str(text)
    return text[:width].ljust(width)


def _header_row() -> str:
    h = (
        f"  {'ID'.ljust(COL['id'])} │ "
        f"{'Name'.ljust(COL['name'])} │ "
        f"{'Age'.ljust(COL['age'])} │ "
        f"{'Course'.ljust(COL['course'])} │ "
        f"{'Email'.ljust(COL['email'])} │ "
        f"{'Created At'.ljust(COL['created'])}"
    )
    return c(h, Colour.YELLOW)


def _divider() -> str:
    total = sum(COL.values()) + (len(COL) - 1) * 3 + 4
    return c("  " + "─" * total, Colour.BLUE)


def print_student_table(students: list):
    """Render a list of Student objects as a formatted console table."""
    if not students:
        info("No student records found.")
        return

    print(f"\n  {c(f'Total students: {len(students)}', Colour.MAGENTA)}")
    print(_divider())
    print(_header_row())
    print(_divider())

    for i, s in enumerate(students):
        row = (
            f"  {_cell(s.student_id, COL['id'])} │ "
            f"{_cell(s.name,       COL['name'])} │ "
            f"{_cell(s.age,        COL['age'])} │ "
            f"{_cell(s.course,     COL['course'])} │ "
            f"{_cell(s.email,      COL['email'])} │ "
            f"{_cell(s.created_at, COL['created'])}"
        )
        colour = Colour.WHITE if i % 2 == 0 else Colour.RESET
        print(c(row, colour))

    print(_divider())
    print()


def print_student_card(s) -> None:
    """Render a single student's details as a formatted card."""
    print(c("\n  ┌─────────────────────────────────────┐", Colour.CYAN))
    print(c("  │        STUDENT DETAILS               │", Colour.CYAN))
    print(c("  ├─────────────────────────────────────┤", Colour.CYAN))
    fields = [
        ("ID",         s.student_id),
        ("Name",       s.name),
        ("Age",        str(s.age)),
        ("Course",     s.course),
        ("Email",      s.email),
        ("Created At", s.created_at),
    ]
    for label, value in fields:
        label_str = c(f"  │  {label:<12}", Colour.YELLOW)
        value_str = c(f": {value:<24}│", Colour.WHITE)
        print(label_str + value_str)
    print(c("  └─────────────────────────────────────┘", Colour.CYAN))
    print()


# ── Input prompt ───────────────────────────────────────────────────────────────

def prompt(label: str, optional: bool = False) -> str:
    """
    Display a styled input prompt.
    If *optional* is True, append "(press Enter to skip)" to the label.
    """
    suffix = c("  (press Enter to skip)", Colour.BLUE) if optional else ""
    tag    = c(f"  ▶  {label}", Colour.CYAN) + suffix + c(": ", Colour.WHITE)
    return input(tag).strip()


def section_title(title: str):
    """Print a bold section heading."""
    bar = "═" * (len(title) + 4)
    print(c(f"\n  ╔{bar}╗", Colour.MAGENTA))
    print(c(f"  ║  {title}  ║", Colour.MAGENTA))
    print(c(f"  ╚{bar}╝\n", Colour.MAGENTA))


def pause():
    """Wait for the user to press Enter before continuing."""
    input(c("\n  Press Enter to continue…", Colour.BLUE))
