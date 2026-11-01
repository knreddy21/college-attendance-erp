from django.contrib import admin
from .models import Department, AcademicYear, Semester, Student, Faculty, Subject, Attendance, Examination, StudentMark, GradingRule
admin.site.register([Department,AcademicYear,Semester,Student,Faculty,Subject,Attendance,Examination,StudentMark,GradingRule])
