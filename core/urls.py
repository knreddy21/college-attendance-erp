from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns=[
 path('login/',auth_views.LoginView.as_view(template_name='registration/login.html'),name='login'),
 path('logout/',auth_views.LogoutView.as_view(),name='logout'),
 path('',views.dashboard,name='dashboard'),
 path('students/',views.student_list,name='student_list'),
 path('students/add/',views.student_create,name='student_create'),
 path('students/<int:pk>/',views.student_profile,name='student_profile'),
 path('students/<int:pk>/edit/',views.student_update,name='student_update'),
 path('students/<int:pk>/delete/',views.student_delete,name='student_delete'),
 path('attendance/',views.attendance_list,name='attendance_list'),
 path('attendance/mark/',views.attendance_mark,name='attendance_mark'),
 path('attendance/bulk/',views.attendance_bulk,name='attendance_bulk'),
 path('attendance/reports/',views.attendance_reports,name='attendance_reports'),
 path('marks/',views.marks_list,name='marks_list'),
 path('marks/bulk/',views.bulk_marks,name='bulk_marks'),
 path('marks/add/',views.mark_create,name='mark_create'),
 path('examinations/add/',views.examination_create,name='examination_create'),
 path('exports/students.xlsx',views.export_students,name='export_students'),
 path('exports/attendance.xlsx',views.export_attendance,name='export_attendance'),
 path('exports/marks.xlsx',views.export_marks,name='export_marks'),
 path('students/<int:pk>/export.xlsx',views.export_student,name='export_student'),
]
