# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Case, When, IntegerField
from django.utils import timezone
from .models import AttendanceEntry, DepartmentAttendance, StudMetaData, AttendanceAvg, HourTable
from datetime import date

@receiver(post_save, sender=AttendanceEntry)
def update_department_attendance(sender, instance, **kwargs):
    # Get department and college from the new attendance record
    dept = instance.stud_dept
    college = instance.college_name

    # Get total students for this department and college from stud_meta_data
    total_students = StudMetaData.objects.filter(stud_dept=dept, college_name=college).count()

    # Filter attendance entries for this department and college
    qs = AttendanceEntry.objects.filter(stud_dept=dept, college_name=college)

    # Aggregate total sessions: count 1 for each non-null hour field
    total_sessions_agg = qs.aggregate(
        total=Sum(
            (
                Case(When(hour_1__isnull=False, then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_2__isnull=False, then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_3__isnull=False, then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_4__isnull=False, then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_5__isnull=False, then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_6__isnull=False, then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_7__isnull=False, then=1), default=0, output_field=IntegerField())
            )
        )
    )
    total_sessions = total_sessions_agg['total'] or 0

    # Aggregate total present: count 1 for each hour that equals '1'
    total_present_agg = qs.aggregate(
        total=Sum(
            (
                Case(When(hour_1='1', then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_2='1', then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_3='1', then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_4='1', then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_5='1', then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_6='1', then=1), default=0, output_field=IntegerField()) +
                Case(When(hour_7='1', then=1), default=0, output_field=IntegerField())
            )
        )
    )
    total_present = total_present_agg['total'] or 0

    # Calculate the average attendance percentage based on total sessions
    if total_sessions > 0:
        avg = (total_present / total_sessions) * 100
    else:
        avg = 0.00

    # Update or create the DepartmentAttendance record for this college and department
    DepartmentAttendance.objects.update_or_create(
        college_name=college,
        department_name=dept,
        defaults={
            'total_students': total_students,
            'total_sessions': total_sessions,
            'total_present': total_present,
            'average_percent': avg,
            'last_updated': timezone.now()
        }
    )


@receiver(post_save, sender=AttendanceEntry)
def update_attendance_avg(sender, instance, **kwargs):
    reg_no = instance.reg_no
    dept = instance.stud_dept
    year = instance.year
    section = instance.section

    # Dynamically determine total_periods based on department
    total_periods = HourTable.objects.filter(at_dept=dept).count() * 7

    # Count attended periods per subject
    attended = AttendanceEntry.objects.filter(REG_NO=reg_no).aggregate(
        sub1=Sum(Case(When(hour_1=1, then=1), default=0)),
        sub2=Sum(Case(When(hour_2=1, then=1), default=0)),
        sub3=Sum(Case(When(hour_3=1, then=1), default=0)),
        sub4=Sum(Case(When(hour_4=1, then=1), default=0)),
        sub5=Sum(Case(When(hour_5=1, then=1), default=0)),
        sub6=Sum(Case(When(hour_6=1, then=1), default=0)),
        sub7=Sum(Case(When(hour_7=1, then=1), default=0)),
    )

    # Calculate percentages
    def calculate_percentage(attended_count):
        return round((attended_count / total_periods) * 100, 2) if total_periods > 0 else 0

    sub1_avg = calculate_percentage(attended['sub1'])
    sub2_avg = calculate_percentage(attended['sub2'])
    sub3_avg = calculate_percentage(attended['sub3'])
    sub4_avg = calculate_percentage(attended['sub4'])
    sub5_avg = calculate_percentage(attended['sub5'])
    sub6_avg = calculate_percentage(attended['sub6'])
    sub7_avg = calculate_percentage(attended['sub7'])

    # Insert or Update Data
    AttendanceAvg.objects.update_or_create(
        reg_no=reg_no,
        defaults={
            "dept": dept,
            "year": year,
            "section": section,
            "sub1": sub1_avg,
            "sub2": sub2_avg,
            "sub3": sub3_avg,
            "sub4": sub4_avg,
            "sub5": sub5_avg,
            "sub6": sub6_avg,
            "sub7": sub7_avg,
            "sdate": date.today(),
            "edate": date.today(),
        }
    )
