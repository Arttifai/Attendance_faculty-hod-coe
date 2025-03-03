from django.urls import path
from . import views

urlpatterns = [
    path('attendance2226/', views.members, name='attendance2226'),
    path('add_faculty/', views.add_faculty, name='add_faculty'),  # Changed from add-faculty to add_faculty
    path('login/',views.index, name='login'),
    path('login/hod/',views.hod_view, name='loginhod'),
    path('hod/student-attendance/', views.hod_student_attendance, name='hod_student_attendance'),
    path('api/subject-wise-attendance/', views.subject_bar_chart, name='subject-wise-attendance'),
    path('api/attendance-line/', views.attendance_line_chart, name='attendance-line-chart'),
    path('api/gender-pie-chart/', views.gender_pie_chart, name='gender_pie_chart'),
    path('login/admin/',views.admin_view, name='loginadmin'),
    path('login/staff/',views.staff_view, name='loginstaff'),
    path('get_subjects/', views.get_subjects, name='get_subjects'),
    path('login/hod/hodinput/', views.upload_excel, name='hodinput'),
    path('upload_subjects/', views.upload_excel_2, name='upload_excel_2'),
    path('logout/', views.logout_view, name='logout'),
]