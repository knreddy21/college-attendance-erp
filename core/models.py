from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Department(models.Model):
    code=models.CharField(max_length=12, unique=True)
    name=models.CharField(max_length=100, unique=True)
    def __str__(self): return f'{self.code} - {self.name}'
    class Meta: ordering=['code']

class AcademicYear(models.Model):
    name=models.CharField(max_length=20, unique=True)
    is_current=models.BooleanField(default=False)
    def __str__(self): return self.name

class Semester(models.Model):
    number=models.PositiveSmallIntegerField(unique=True, validators=[MinValueValidator(1),MaxValueValidator(12)])
    name=models.CharField(max_length=30, blank=True)
    def __str__(self): return self.name or f'Semester {self.number}'

class Student(models.Model):
    student_id=models.CharField(max_length=12, unique=True)
    roll_number=models.CharField(max_length=30, unique=True)
    full_name=models.CharField(max_length=150)
    profile_image=models.ImageField(upload_to='students/', blank=True, null=True)
    GENDER=[('M','Male'),('F','Female'),('O','Other')]
    gender=models.CharField(max_length=1, choices=GENDER, blank=True)
    date_of_birth=models.DateField(blank=True, null=True)
    email=models.EmailField(blank=True)
    mobile=models.CharField(max_length=20, blank=True)
    parent_name=models.CharField(max_length=150, blank=True)
    parent_mobile=models.CharField(max_length=20, blank=True)
    department=models.ForeignKey(Department,on_delete=models.PROTECT,related_name='students',null=True,blank=True)
    course=models.CharField(max_length=100, blank=True)
    academic_year=models.ForeignKey(AcademicYear,on_delete=models.SET_NULL,null=True,blank=True)
    semester=models.ForeignKey(Semester,on_delete=models.SET_NULL,null=True,blank=True)
    section=models.CharField(max_length=10,blank=True)
    admission_date=models.DateField(default=timezone.localdate)
    address=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.roll_number} - {self.full_name}'
    class Meta: ordering=['roll_number']

class Faculty(models.Model):
    employee_id=models.CharField(max_length=20,unique=True)
    full_name=models.CharField(max_length=150)
    email=models.EmailField(blank=True)
    mobile=models.CharField(max_length=20,blank=True)
    department=models.ForeignKey(Department,on_delete=models.SET_NULL,null=True,blank=True)
    def __str__(self): return f'{self.employee_id} - {self.full_name}'

class Subject(models.Model):
    code=models.CharField(max_length=20,unique=True)
    name=models.CharField(max_length=120)
    department=models.ForeignKey(Department,on_delete=models.CASCADE,related_name='subjects')
    semester=models.ForeignKey(Semester,on_delete=models.SET_NULL,null=True,blank=True)
    faculty=models.ForeignKey(Faculty,on_delete=models.SET_NULL,null=True,blank=True)
    def __str__(self): return f'{self.code} - {self.name}'
    class Meta: ordering=['code']

class Attendance(models.Model):
    STATUS=[('P','Present'),('A','Absent'),('OD','On Duty')]
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='attendance_records')
    subject=models.ForeignKey(Subject,on_delete=models.PROTECT,related_name='attendance_records')
    date=models.DateField()
    status=models.CharField(max_length=2,choices=STATUS,default='P')
    marked_by=models.ForeignKey(Faculty,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['student','subject','date'],name='unique_student_subject_attendance_date')]
        ordering=['-date','student__roll_number']
    def __str__(self): return f'{self.student} {self.subject} {self.date} {self.status}'

class Examination(models.Model):
    TYPES=[('IN1','Internal 1'),('IN2','Internal 2'),('MID','Mid Examination'),('ASSIGN','Assignment'),('PRACT','Practical'),('SEM','Semester Examination')]
    name=models.CharField(max_length=120)
    exam_type=models.CharField(max_length=10,choices=TYPES)
    academic_year=models.ForeignKey(AcademicYear,on_delete=models.SET_NULL,null=True,blank=True)
    semester=models.ForeignKey(Semester,on_delete=models.SET_NULL,null=True,blank=True)
    date=models.DateField(blank=True,null=True)
    def __str__(self): return self.name

class GradingRule(models.Model):
    grade=models.CharField(max_length=3,unique=True)
    min_percentage=models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0),MaxValueValidator(100)])
    max_percentage=models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0),MaxValueValidator(100)])
    is_pass=models.BooleanField(default=True)
    class Meta: ordering=['-min_percentage']
    def __str__(self): return f'{self.grade}: {self.min_percentage}-{self.max_percentage}%'

class StudentMark(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE,related_name='marks')
    subject=models.ForeignKey(Subject,on_delete=models.PROTECT)
    examination=models.ForeignKey(Examination,on_delete=models.CASCADE)
    max_marks=models.DecimalField(max_digits=7,decimal_places=2,validators=[MinValueValidator(0)])
    obtained_marks=models.DecimalField(max_digits=7,decimal_places=2,validators=[MinValueValidator(0)])
    class Meta:
        constraints=[models.UniqueConstraint(fields=['student','subject','examination'],name='unique_student_subject_exam_mark')]
    @property
    def percentage(self):
        return (self.obtained_marks / self.max_marks * 100) if self.max_marks else 0
    @property
    def grade_rule(self):
        return GradingRule.objects.filter(min_percentage__lte=self.percentage,max_percentage__gte=self.percentage).first()
    @property
    def result_status(self):
        rule=self.grade_rule
        return 'Pass' if rule and rule.is_pass else 'Fail'
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.obtained_marks > self.max_marks:
            raise ValidationError('Obtained marks cannot exceed maximum marks.')
