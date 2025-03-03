from django.db import models
from django.contrib.auth.hashers import make_password


class Faculty(models.Model):
    DESIGNATION_CHOICES = [
        ("HOD", "Head of Department"),
        ("STAFF/AP", "Staff/AP"),
        ("STAFF/ASP", "Staff/ASP"),
        ("LAB INCHARGE", "Lab Incharge"),
        ("COE", "Controller of Examinations"),
        ("PRINCIPAL", "Principal"),
        ("ADMIN", "Administrator"),
    ]
    
    FLAG_CHOICES = [
        ("x", "Inactive"),
        ("o", "Active"),
    ]
    
    INSTITUTION_CHOICES = [
        ("PAAVAI ENGINEERING COLLEGE", "Paavai Engineering College"),
        ("PAAVAI COLLEGE OF ENGINEERING", "Paavai College of Engineering"),
    ]
    
    INSTITUTION_NUMBER_CHOICES = [
        ("6221", "6221"),
        ("6220", "6220"),
    ]

    id = models.AutoField(primary_key=True)
    staff_name = models.CharField(max_length=35, db_column="Staff_Name")
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES, db_column="designation")
    department = models.CharField(max_length=35, blank=True, null=True, db_column="department")
    
    handling_subject1 = models.CharField(max_length=60, blank=True, null=True, db_column="Handling_Subject1")
    handling_subject2 = models.CharField(max_length=60, blank=True, null=True, db_column="Handling_Subject2")
    handling_subject3 = models.CharField(max_length=60, blank=True, null=True, db_column="Handling_Subject3")
    handling_subject4 = models.CharField(max_length=60, blank=True, null=True, db_column="Handling_Subject4")
    handling_subject5 = models.CharField(max_length=60, blank=True, null=True, db_column="Handling_Subject5")

    handling_department1 = models.CharField(max_length=50, blank=True, null=True, db_column="Handling_Department1")
    handling_department2 = models.CharField(max_length=50, blank=True, null=True, db_column="Handling_Department2")
    handling_department3 = models.CharField(max_length=50, blank=True, null=True, db_column="Handling_Department3")

    flag_f = models.CharField(
        max_length=1, 
        choices=FLAG_CHOICES, 
        db_column="flagF", 
        default="o"  # Default value for active
    )
    date_of_joining = models.DateField(db_column="Date_of_joining")
    institution_name = models.CharField(max_length=30, blank=True, null=True, choices=INSTITUTION_CHOICES, db_column="instution_name")
    institution_number = models.CharField(max_length=4, blank=True, null=True, choices=INSTITUTION_NUMBER_CHOICES, db_column="instution_number")

    class Meta:
        managed = False  # Indicates Django won't manage the table
        db_table = 'faculty'  # Connects to the existing database table

    def __str__(self):
        return f"{self.staff_name} - {self.department}"



class FacultyLogin(models.Model):
    id = models.OneToOneField(
        'Faculty',  # Replace with the actual import or app label if necessary
        on_delete=models.CASCADE,
        db_column="id",  # Matches the column in the database
        primary_key=True  # Ensures this field is the primary key for FacultyLogin
    )
    name = models.CharField(max_length=35)
    username = models.CharField(max_length=35, unique=True)
    password = models.CharField(max_length=128)  # Adjust length to fit hashed password

    class Meta:
        db_table = 'faculty_login'  # Matches the name of the existing table
        managed = False  # Prevent Django from trying to create or alter this table

    def save(self, *args, **kwargs):
        # Hash the password if it is not already hashed
        if not self.password.startswith('pbkdf2_'):  # Ensures password is hashed only once
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class StudMetaData(models.Model):
    REG_NO = models.BigIntegerField(primary_key=True)
    stud_name = models.CharField(max_length=50)
    college_name = models.CharField(max_length=50)
    degree = models.CharField(max_length=10)
    stud_dept = models.CharField(max_length=50)
    year = models.IntegerField()
    section = models.CharField(max_length=5)
    gender = models.CharField(max_length=10)
    join_year = models.IntegerField()
    passout_year = models.IntegerField()

    def __str__(self):
        return self.stud_name

    class Meta:
        db_table = 'stud_meta_data'  # Match the exact table name in your database
        managed = False

class HourTable(models.Model):
    hour_id = models.AutoField(primary_key=True)  # AUTO_INCREMENT primary key
    at_year = models.IntegerField()
    at_dept = models.CharField(max_length=35)
    at_day_order = models.IntegerField()
    sub1 = models.CharField(max_length=50)
    sub2 = models.CharField(max_length=50)
    sub3 = models.CharField(max_length=50)
    sub4 = models.CharField(max_length=50)
    sub5 = models.CharField(max_length=50)
    sub6 = models.CharField(max_length=50)
    sub7 = models.CharField(max_length=50)
    at_sdate = models.DateField()
    at_edate = models.DateField()

    def __str__(self):
        return f"{self.at_year} - {self.at_dept}"

    class Meta:
        db_table = 'hour_table'
        managed = False  # This ensures the table is not managed by Django migrations
        #unique_together = ['at_dept', 'at_sdate', 'at_edate']  # Enforces the uniqueness constraint


class AttendanceEntry(models.Model):
    attend_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    reg_no = models.BigIntegerField()  # This will reference `stud_meta_data`
    college_name = models.CharField(max_length=50)
    stud_dept = models.CharField(max_length=50)
    year = models.IntegerField()
    section = models.CharField(max_length=5)
    attend_date = models.DateField()
    day_order = models.IntegerField()

    # Hourly attendance with nullable values
    hour_1 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])
    hour_2 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])
    hour_3 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])
    hour_4 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])
    hour_5 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])
    hour_6 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])
    hour_7 = models.CharField(max_length=2, null=True, choices=[('1', 'Present'), ('0', 'Absent'), ('OD', 'On Duty')])

    # Mode handling fields with nullable values
    Modes = [
        ('Theory', 'theory'),
        ('Practical', 'practical'),
        ('Others', 'others'),
    ]
    mode_handle1 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle1')
    mode_handle2 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle2')
    mode_handle3 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle3')
    mode_handle4 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle4')
    mode_handle5 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle5')
    mode_handle6 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle6')
    mode_handle7 = models.CharField(max_length=10, choices=Modes, null=True, db_column='mode_handle7')

    sdate = models.DateField()
    edate = models.DateField()

    def __str__(self):
        return f"{self.reg_no} - {self.stud_dept}"

    class Meta:
        db_table = 'attendance_entry'
        managed = False  # Table is not managed by Django

class SubjectHandle(models.Model):
    sh_id = models.AutoField(primary_key=True)  # Auto-increment primary key
    faculty_name = models.CharField(max_length=100)  # Faculty name
    dept = models.CharField(max_length=50)  # Department
    year = models.PositiveIntegerField()  # Year of the course (e.g., 1, 2, 3, 4)
    subject = models.CharField(max_length=100)  # Subject being handled
    day_order = models.PositiveIntegerField()  # Day order (e.g., 1 for Monday, 2 for Tuesday)
    hour = models.PositiveIntegerField()  # Hour of the day (e.g., 1 for the first hour)
    MODE_CHOICES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('others', 'Others')
    ]
    mode_of_handle = models.CharField(max_length=10, choices=MODE_CHOICES)  # Mode of handling
    sdate = models.DateField()  # Start date
    edate = models.DateField()  # End date

    def __str__(self):
        return f"{self.faculty_name} - {self.subject}"

    class Meta:
        managed = False  # Django will not manage the table
        db_table = 'subject_handle'


class DepartmentSubjects(models.Model):
    dept = models.CharField(max_length=50, db_column="dept")  # Department name
    sub1 = models.CharField(max_length=100, db_column="sub1", blank=True, null=True)
    sub2 = models.CharField(max_length=100, db_column="sub2", blank=True, null=True)
    sub3 = models.CharField(max_length=100, db_column="sub3", blank=True, null=True)
    sub4 = models.CharField(max_length=100, db_column="sub4", blank=True, null=True)
    sub5 = models.CharField(max_length=100, db_column="sub5", blank=True, null=True)
    sub6 = models.CharField(max_length=100, db_column="sub6", blank=True, null=True)
    st_date = models.DateField(db_column="stDate", blank=True, null=True)  # Start date
    ed_date = models.DateField(db_column="edDate", blank=True, null=True)  # End date
    year = models.IntegerField(db_column="year")  # New year field

    class Meta:
        managed = False  # Django won't manage this table if it already exists
        db_table = 'department_subjects'  # Name of the existing MySQL table

    def __str__(self):
        return f"{self.dept} - Year {self.year} ({self.st_date} to {self.ed_date})"

class DepartmentAttendance(models.Model):
    college_name = models.CharField(max_length=50)
    department_name = models.CharField(max_length=50, unique=True)
    total_students = models.PositiveIntegerField(default=0)
    total_sessions = models.PositiveIntegerField(default=0)
    total_present = models.PositiveIntegerField(default=0)
    average_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'department_attendance'  # or 'department_subjects' if that's really your table name

    def __str__(self):
        return f"{self.department_name} - {self.average_percent:.2f}%"
    

class AttendanceAvg(models.Model):
    reg_no = models.CharField(max_length=50)  # Increased size
    dept = models.CharField(max_length=20)  # Increased size
    year = models.IntegerField()
    section = models.CharField(max_length=5)
    sub1 = models.FloatField(default=0)
    sub2 = models.FloatField(default=0)
    sub3 = models.FloatField(default=0)
    sub4 = models.FloatField(default=0)
    sub5 = models.FloatField(default=0)
    sub6 = models.FloatField(default=0)
    sub7 = models.FloatField(default=0)
    sdate = models.DateField()
    edate = models.DateField()

    class Meta:
        managed = False  # Since we manually modified MySQL
        db_table = 'attendance_avg'
    def __str__(self):
        return f"{self.reg_no} - {self.dept} ({self.year})"
