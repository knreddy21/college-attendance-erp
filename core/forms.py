from django import forms
from .models import Student, Attendance, Faculty, Subject, Examination, StudentMark, Department
class DateInput(forms.DateInput):
    input_type='date'
class StudentForm(forms.ModelForm):
    class Meta:
        model=Student
        fields='__all__'
        widgets={'date_of_birth':DateInput(),'admission_date':DateInput()}
class AttendanceForm(forms.ModelForm):
    class Meta:
        model=Attendance
        fields=['student','subject','date','status']
        widgets={'date':DateInput()}
class FacultyForm(forms.ModelForm):
    class Meta: model=Faculty; fields='__all__'
class SubjectForm(forms.ModelForm):
    class Meta: model=Subject; fields='__all__'
class ExaminationForm(forms.ModelForm):
    class Meta:
        model=Examination; fields='__all__'; widgets={'date':DateInput()}
class StudentMarkForm(forms.ModelForm):
    class Meta: model=StudentMark; fields='__all__'
