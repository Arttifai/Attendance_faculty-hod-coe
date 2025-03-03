from django.contrib import admin
from .models import Faculty, FacultyLogin, StudMetaData, HourTable, AttendanceEntry, SubjectHandle, DepartmentSubjects, DepartmentAttendance, AttendanceAvg

class FacultyLoginAdmin(admin.ModelAdmin):
    search_fields = ['username']  # Search by username for FacultyLogin

class FacultyAdmin(admin.ModelAdmin):
    search_fields = ['staff_name']  # Search by staff name for Facult
    list_display = ['staff_name', 'designation', 'department', 'handling_subjects', 'institution_name']
    list_filter = ['designation', 'institution_name']

    def handling_subjects(self, obj):
        """
        Combine all subject fields into one string for display in the admin panel.
        """
        subjects = [
            obj.handling_subject1,
            obj.handling_subject2,
            obj.handling_subject3,
            obj.handling_subject4,
            obj.handling_subject5,
        ]
        return ", ".join([subject for subject in subjects if subject]) or "No Subjects"
    handling_subjects.short_description = 'Handling Subjects'

class HourTableAdmin(admin.ModelAdmin):
    search_fields = ['at_year', 'at_dept']  # Search by year and department for HourTable
    list_filter = ['at_year', 'at_dept']    # Add filter sidebar with checkboxes for year and department

class StudMetaDataAdmin(admin.ModelAdmin):
    search_fields = ['stud_name']                # Search by name for students
    list_filter = ['year', 'stud_dept', 'college_name']  # Filter sidebar for year, department, and college

class AttendanceEntryAdmin(admin.ModelAdmin):
    list_display = ['reg_no', 'college_name', 'stud_dept', 'year']
    list_filter = ['stud_dept', 'year']


admin.site.register(Faculty, FacultyAdmin)
admin.site.register(FacultyLogin, FacultyLoginAdmin)
admin.site.register(StudMetaData, StudMetaDataAdmin)
admin.site.register(HourTable, HourTableAdmin)
admin.site.register(AttendanceEntry, AttendanceEntryAdmin)
admin.site.register(SubjectHandle)
admin.site.register(DepartmentSubjects)
admin.site.register(DepartmentAttendance)
admin.site.register(AttendanceAvg)


# Register your models here.
