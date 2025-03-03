# views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from .models import Faculty, FacultyLogin, StudMetaData, HourTable, AttendanceEntry, DepartmentSubjects, DepartmentAttendance, AttendanceAvg
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.decorators import login_required
from .forms import ExcelUploadForm
from django.contrib.auth.hashers import check_password 
import json
from django.utils.dateparse import parse_date
from django.db.models import Count, Avg, Sum, Case, When, Q, IntegerField
from django.views.decorators.cache import never_cache

def disable_cache(view_func):
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return wrapper



@csrf_protect
def members(request):
    if request.method == 'POST':
        try:
            print("Form Data:", request.POST)  # Debugging
            institution_name = request.POST.get('college')
            institution_number = "6221" if institution_name == "PAAVAI ENGINEERING COLLEGE" else "6220"
            
            faculty = Faculty(
                staff_name=request.POST.get('name'),
                designation=request.POST.get('position'),
                department=request.POST.get('department'),
                handling_subject=request.POST.get('subject_handling'),
                date_of_joining=request.POST.get('date_of_join'),
                institution_name=institution_name,
                institution_number=institution_number,
                flag_f='o'
            )
            faculty.save()

            # Verify that the instance is saved
            print("Saved Faculty:", faculty)

            faculty_login = FacultyLogin(
                id=faculty,  # Associate the Faculty object (faculty) with FacultyLogin
                name=request.POST.get('name'),
                username=request.POST.get('username'),
                password=request.POST.get('password')
            )
            faculty_login.save()
            print("Saved FacultyLogin:", faculty_login)

            messages.success(request, "Faculty member added successfully!")
            return redirect('add_faculty')
        except Exception as e:
            print("Error:", e)  # Log the error for debugging
            messages.error(request, f"Error saving faculty: {str(e)}")
    return render(request, 'staffentire.html')

@csrf_protect
def add_faculty(request):
    # Get all faculty members and their login information
    faculties = Faculty.objects.all()
    return render(request, 'add_faculty.html', {'faculties': faculties})


@csrf_protect
@disable_cache
@never_cache
def index(request):
    #facultiesLogin = Faculty.objects.all()
    if request.method == 'GET':
        # Clear session on GET requests (back button or direct access)
        request.session.flush()
    if request.method == 'POST':
        ind_name = request.POST.get('ind_user')
        ind_pass = request.POST.get('ind_password')
        
        print(ind_name, ind_pass)  # Debugging
        
        try:
            # Get the FacultyLogin object by username
            Login_User = FacultyLogin.objects.get(username=ind_name)
            
            # Check if the password matches
            if check_password(ind_pass, Login_User.password):
            #if ind_pass == Login_User.password:
                # Get the corresponding Faculty object
                LoggedUser = Login_User.id  # Login_User is already a Faculty instance due to the OneToOneField
                # Redirect based on designation
                request.session['user_id'] = LoggedUser.id
                request.session['username'] = ind_name
                if LoggedUser.designation == 'HOD':
                    return redirect('loginhod')
                elif LoggedUser.designation == 'ADMIN':
                    return redirect('loginadmin')
                elif LoggedUser.designation == 'STAFF/AP' or LoggedUser.designation == 'STAFF/ASP' or LoggedUser.designation == 'HOD':
                    return redirect('loginstaff')
            else:
                # Password mismatch
                return render(request, 'index.html', {'error': 'Invalid credentials'})
        
        except FacultyLogin.DoesNotExist:
            # User not found
            return render(request, 'index.html', {'error': 'Invalid credentials'})
        
    return render(request, 'index.html')


@disable_cache
def hod_view(request):
    if not request.session.get('user_id'):
        return redirect('logout')
    # Get user details from session
    user_id = request.session.get('user_id')
    user = Faculty.objects.filter(id=user_id).first()

    # Get institution and department
    institution_name = user.institution_name
    department = user.department
    #print(institution_name, department)

    # Fetch student data based on institution and department
    students = StudMetaData.objects.filter(college_name=institution_name, stud_dept=department)

    # Total count of students
    total_students = students.count()

    # Gender-wise count
    gender_counts = students.values('gender').annotate(count=Count('gender'))

    # Create a dictionary to easily access gender counts
    gender_data = {gender['gender']: gender['count'] for gender in gender_counts}
    #print(total_students, gender_counts)

    # Retrieve the department attendance record for the given college and department
    dept_attendance = DepartmentAttendance.objects.filter(
        college_name=institution_name, 
        department_name=department
    ).first()
    
    # Extract average attendance if available
    avg_attendance = dept_attendance.average_percent if dept_attendance else None

    # Pass data to the template
    return render(request, 'hod.html', {
        'students': students,
        'total_students': total_students,
        'gender_data': gender_data,
        'avg_attendance': avg_attendance,
    })



def hod_student_attendance(request):
    """
    Returns a JSON response grouping students (from the HOD's department) by attendance percentage.
    Categories are:
      - below60: attendance percentage < 60%
      - between60and80: attendance between 60% and 80% (inclusive)
      - above80: attendance percentage > 80%
    """
    if not request.session.get('user_id'):
        return redirect('logout')
    # Get user details from session
    user_id = request.session.get('user_id')
    user = Faculty.objects.filter(id=user_id).first()
    
        # Get the HOD's department (adjust according to your user model)
    hod_dept = user.department
    #print(hod_dept)

    # Filter attendance records for the HOD's department.
    # (Both attendance_entry and stud_meta_data have the stud_dept field.)
    qs = AttendanceEntry.objects.filter(stud_dept=hod_dept)

    # Aggregate attendance data by student (grouped by REG_NO).
    # We sum up the number of hours marked as '1' (present) across all records,
    # and we also sum up the total number of hour fields (assuming non-null fields count as a class).
    aggregated = qs.values('reg_no').annotate(
    # Sum up present hours for each hour column.
    present_hour_1=Sum(Case(When(hour_1='1', then=1), default=0, output_field=IntegerField())),
    present_hour_2=Sum(Case(When(hour_2='1', then=1), default=0, output_field=IntegerField())),
    present_hour_3=Sum(Case(When(hour_3='1', then=1), default=0, output_field=IntegerField())),
    present_hour_4=Sum(Case(When(hour_4='1', then=1), default=0, output_field=IntegerField())),
    present_hour_5=Sum(Case(When(hour_5='1', then=1), default=0, output_field=IntegerField())),
    present_hour_6=Sum(Case(When(hour_6='1', then=1), default=0, output_field=IntegerField())),
    present_hour_7=Sum(Case(When(hour_7='1', then=1), default=0, output_field=IntegerField())),
    # Count the total number of hours recorded (if a value is not null, count it as 1)
    total_hour_1=Sum(Case(When(hour_1__isnull=False, then=1), default=0, output_field=IntegerField())),
    total_hour_2=Sum(Case(When(hour_2__isnull=False, then=1), default=0, output_field=IntegerField())),
    total_hour_3=Sum(Case(When(hour_3__isnull=False, then=1), default=0, output_field=IntegerField())),
    total_hour_4=Sum(Case(When(hour_4__isnull=False, then=1), default=0, output_field=IntegerField())),
    total_hour_5=Sum(Case(When(hour_5__isnull=False, then=1), default=0, output_field=IntegerField())),
    total_hour_6=Sum(Case(When(hour_6__isnull=False, then=1), default=0, output_field=IntegerField())),
    total_hour_7=Sum(Case(When(hour_7__isnull=False, then=1), default=0, output_field=IntegerField())),
    )

        # Prepare the result dictionary with three groups.
    result = {
        'below60': [],
        'between60and80': [],
        'above80': [],
    }

    for record in aggregated:
        reg_no = record['reg_no']
        # Calculate the total present hours by summing all the present_hour values.
        present_count = (
            record['present_hour_1'] +
            record['present_hour_2'] +
            record['present_hour_3'] +
            record['present_hour_4'] +
            record['present_hour_5'] +
            record['present_hour_6'] +
            record['present_hour_7']
        )
        # Calculate the total hours recorded for the student.
        total_count = (
            record['total_hour_1'] +
            record['total_hour_2'] +
            record['total_hour_3'] +
            record['total_hour_4'] +
            record['total_hour_5'] +
            record['total_hour_6'] +
            record['total_hour_7']
        )

        # Compute attendance percentage.
        percentage = (present_count / total_count * 100) if total_count > 0 else 0

        # Retrieve the student's meta data to get the name.
        try:
            student = StudMetaData.objects.get(REG_NO=reg_no, stud_dept=hod_dept)
        except StudMetaData.DoesNotExist:
            # Skip if the student does not belong to the HOD's department or record is missing.
            continue

        # Prepare student info to send back to the client.
        student_info = {
            'REG_NO': reg_no,
            'stud_name': student.stud_name,
            'year' : student.year,
            'percentage': round(percentage, 2)
        }

        # Group the student based on their attendance percentage.
        if percentage < 60:
            result['below60'].append(student_info)
        elif 60 <= percentage <= 80:
            result['between60and80'].append(student_info)
        elif percentage > 80:
            result['above80'].append(student_info)
        # Note: Students with attendance between 50 and 70% will not be added.
        
    return JsonResponse(result)


def attendance_line_chart(request):
    user_id = request.session.get('user_id')
    user = Faculty.objects.filter(id=user_id).first()
    if not request.session.get('user_id'):
        return redirect('logout')

    if not user:
        return JsonResponse({"status": "error", "message": "Invalid user"}, status=400)
    
    dept_name = user.department
    # Get total number of students in the dataset
    total_students = AttendanceEntry.objects.filter(stud_dept=dept_name).count()

    if total_students == 0:
        return JsonResponse({
            "labels": ["1", "2", "3", "4", "5", "6", "7"],
            "values": [0, 0, 0, 0, 0, 0, 0]
        })

    # Count students present per hour
    present_counts = AttendanceEntry.objects.filter(stud_dept=dept_name).aggregate(
        hour_1=Sum(Case(When(hour_1=1, then=1), default=0)),
        hour_2=Sum(Case(When(hour_2=1, then=1), default=0)),
        hour_3=Sum(Case(When(hour_3=1, then=1), default=0)),
        hour_4=Sum(Case(When(hour_4=1, then=1), default=0)),
        hour_5=Sum(Case(When(hour_5=1, then=1), default=0)),
        hour_6=Sum(Case(When(hour_6=1, then=1), default=0)),
        hour_7=Sum(Case(When(hour_7=1, then=1), default=0)),
    )

    # Calculate the percentage correctly
    values = [
        round((present_counts[f"hour_{i}"] / total_students) * 100, 2)
        if total_students > 0 else 0
        for i in range(1, 8)
    ]

    return JsonResponse({
        "labels": ["1", "2", "3", "4", "5", "6", "7"],
        "values": values
    })



def gender_pie_chart(request):
    user_id = request.session.get('user_id')
    user = Faculty.objects.filter(id=user_id).first()
    if not request.session.get('user_id'):
        return redirect('logout')

    if not user:
        return JsonResponse({"status": "error", "message": "Invalid user"}, status=400)

    dept_name = user.department

    # Count total days (unique attendance dates)
    total_days = AttendanceEntry.objects.filter(stud_dept=dept_name).values('attend_date').distinct().count()

    if total_days == 0:
        return JsonResponse({"status": "error", "message": "No attendance records found"}, status=400)

    # Calculate total possible attendance
    male_students = StudMetaData.objects.filter(gender='m', stud_dept=dept_name).count()
    female_students = StudMetaData.objects.filter(gender='f', stud_dept=dept_name).count()
    
    total_male_possible = male_students * 7 * total_days
    total_female_possible = female_students * 7 * total_days

    # Count actual attendance
    male_count = AttendanceEntry.objects.filter(
        reg_no__in=StudMetaData.objects.filter(gender='m', stud_dept=dept_name).values('REG_NO')
    ).filter(
        Q(hour_1=1) | Q(hour_2=1) | Q(hour_3=1) | Q(hour_4=1) | Q(hour_5=1) | Q(hour_6=1) | Q(hour_7=1)
    ).count()

    female_count = AttendanceEntry.objects.filter(
        reg_no__in=StudMetaData.objects.filter(gender='f', stud_dept=dept_name).values('REG_NO')
    ).filter(
        Q(hour_1=1) | Q(hour_2=1) | Q(hour_3=1) | Q(hour_4=1) | Q(hour_5=1) | Q(hour_6=1) | Q(hour_7=1)
    ).count()

    # Compute attendance percentages
    #print(male_students, total_days,'\n')
    #print(male_count, total_male_possible)
    avg_male = round((male_count / total_male_possible) * 100, 2) if total_male_possible > 0 else 0
    avg_female = round((female_count / total_female_possible) * 100, 2) if total_female_possible > 0 else 0

    return JsonResponse({
        "labels": ["Male", "Female"],
        "values": [avg_male, avg_female]
    })



def subject_bar_chart(request):
    # Validate user and session
    user_id = request.session.get('user_id')
    user = Faculty.objects.filter(id=user_id).first()
    if not user:
        return redirect('logout')
    
    dept = user.department

    # Get the year from GET parameters or use the user's year
    year_param = request.GET.get('year')
    if not year_param:
        year = user.year if hasattr(user, 'year') else None
    else:
        year = int(year_param)
    if not year:
        return JsonResponse({"status": "error", "message": "Year not specified"}, status=400)

    data = AttendanceAvg.objects.filter(dept=dept, year=year).values(
        "sub1", "sub2", "sub3", "sub4", "sub5", "sub6", "sub7"
    )

    if not data.exists():
        return JsonResponse({"status": "error", "message": "No data found"}, status=404)

    avg_data = data.aggregate(
        sub1_avg=Sum("sub1") / data.count(),
        sub2_avg=Sum("sub2") / data.count(),
        sub3_avg=Sum("sub3") / data.count(),
        sub4_avg=Sum("sub4") / data.count(),
        sub5_avg=Sum("sub5") / data.count(),
        sub6_avg=Sum("sub6") / data.count(),
        sub7_avg=Sum("sub7") / data.count(),
    )

    return JsonResponse({"averages": avg_data})






@disable_cache
def admin_view(request):
    if not request.session.get('user_id'):
        return redirect('logout')
    return render(request, 'adminpanel.html')


@csrf_exempt  # Required for AJAX POST requests
@disable_cache
def staff_view(request):
    user_id = request.session.get('user_id')
    user = Faculty.objects.filter(id=user_id).first()
    # Fetch all the department subjects
    dept_subs = DepartmentSubjects.objects.all()

    # Initialize an empty dictionary
    dept_dict = {}

    # Loop through each row and build the dictionary
    for dept_sub in dept_subs:
        dept_dict[dept_sub.dept] = [
            dept_sub.year,
            dept_sub.sub1,
            dept_sub.sub2,
            dept_sub.sub3,
            dept_sub.sub4,
            dept_sub.sub5,
            dept_sub.sub6
        ]

    # Now dept_dict contains the results as a dictionary

    #print(dept_dict)
    if not request.session.get('user_id'):
        return redirect('logout')

    if not user:
        return JsonResponse({"status": "error", "message": "Invalid user"}, status=400)

    institution_name = user.institution_name
    subjects = [user.handling_subject1, user.handling_subject2, user.handling_subject3, user.handling_subject4, user.handling_subject5]
    subjects = list(filter(None, subjects))
    hand_dept = [user.handling_department1, user.handling_department2, user.handling_department3]
    hand_dept = list(filter(None,hand_dept))

    if request.method == 'POST':
        try:

            data = json.loads(request.body)
            print("Received data:", data)  # Debugging line

            if 'selected_students' in data:  # Handling attendance marking
                selected_students = data.get('selected_students', [])
                attend_date = parse_date(data.get('date'))
                college_name = institution_name
                stud_dept = data.get('department')
                year = data.get('year')
                section = data.get('section')
                hour = data.get('hour')
                day_order = data.get('day_order')
                mode_handle = data.get('mode_handle')


                print("Attendance data:")  # Debugging line
                print("selected_students:", selected_students)
                print("attend_date:", attend_date)
                print("college_name:", college_name)
                print("stud_dept:", stud_dept)
                print("year:", year)
                print("section:", section)
                print("hour:", hour)
                print("day_order:", day_order)

                all_students = list(StudMetaData.objects.filter(
                    college_name=college_name,
                    stud_dept=stud_dept,
                    year=year,
                    section=section
                ).values_list('REG_NO', flat=True))
                old_attendance = AttendanceEntry.objects.filter(
                    college_name=college_name,
                    stud_dept=stud_dept,
                    year=year,
                    section=section,
                    attend_date=attend_date
                ).values("hour_1","hour_2","hour_3","hour_4","hour_5","hour_6","hour_7",)
                old_attendance = list(old_attendance)

                absent_students = selected_students
                present_students = list(set(all_students) - set(absent_students))
                print(absent_students)
                print(present_students)

                for REG_NO in all_students:
                    status = '0' if REG_NO in absent_students else '1'
                    
                    # Prepare the field name for the specific hour column dynamically
                    hour_column = f"hour_{hour}"  # e.g., 'hour_1', 'hour_2', etc.
                    mode_column = f"mode_handle{hour}"
                    
                    # Update or create each attendance entry
                    defaults = {
                        hour_column: status,  # Set the appropriate hour dynamically
                        'sdate': '2024-05-12',
                        'edate': '2025-01-08',
                        mode_column: mode_handle,
                    }
                    
                    AttendanceEntry.objects.update_or_create(
                        reg_no=REG_NO,
                        college_name=college_name,
                        stud_dept=stud_dept,
                        year=year,
                        section=section,
                        attend_date=attend_date,
                        day_order=day_order,
                        defaults=defaults
                    )


                return JsonResponse({'success': True, 'message': 'Attendance marked successfully!'})

            else:  # Handling student filtering
                department = data.get("department", "")
                year = data.get("year", "")
                section = data.get("section", "")

                print("Filtering data:")  # Debugging line
                print("department:", department)
                print("year:", year)
                print("section:", section)

                students = StudMetaData.objects.filter(college_name=institution_name)

                if department:
                    students = students.filter(stud_dept=department)
                if year:
                    students = students.filter(year=year)
                if section:
                    students = students.filter(section=section)

                students_data = list(students.values("REG_NO", "stud_name"))
                print(students_data)

                return JsonResponse({
                    "status": "success",
                    "students_data": students_data,
                })

        except Exception as e:
            print("Error:", str(e))  # Debugging line
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    if request.method == "GET":
        department = request.GET.get("department", "")
        year = request.GET.get("year", "")
        section = request.GET.get("section", "")

        # Base queryset for all students in the institution
        students = StudMetaData.objects.filter(college_name=institution_name)

        # Check if at least one parameter is provided to filter
        filters_applied = False
        if department:
            students = students.filter(stud_dept=department)
            filters_applied = True
        if year:
            students = students.filter(year=year)
            filters_applied = True
        if section:
            students = students.filter(section=section)
            filters_applied = True

        # If no filter was applied, show a message or return no data
        if not filters_applied:
            students = students.none()  # Returns an empty queryset

        return render(request, "staffpanel_V3.html", {"students": students, "subjects": subjects, "hand_dept":hand_dept, "dept_dict":dept_dict})



    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

def get_subjects(request):
    department = request.GET.get('department')
    year = request.GET.get('year')

    # Get subjects for the selected department & year
    subjects_data = DepartmentSubjects.objects.filter(dept=department, year=year).first()
    
    if subjects_data:
        all_subjects = [subjects_data.sub1, subjects_data.sub2, subjects_data.sub3, 
                        subjects_data.sub4, subjects_data.sub5, subjects_data.sub6]
        all_subjects = [sub for sub in all_subjects if sub]  # Remove empty values

        # Get all handling subjects from the Faculty model
        faculty_subjects = Faculty.objects.values_list(
            "handling_subject1", "handling_subject2", "handling_subject3", 
            "handling_subject4", "handling_subject5"
        )

        # Flatten and clean the list
        allocated_subjects = set(sub for subjects in faculty_subjects for sub in subjects if sub)

        # Filter subjects that match the faculty's allocated subjects
        subjects = [sub for sub in all_subjects if sub in allocated_subjects]
    else:
        subjects = []

    return JsonResponse(subjects, safe=False)


def upload_excel(request):
    if request.method == "POST":
        print(f"Request Files: {request.FILES}")  # Check what files are received
        # Check if the Excel file is provided
        if "excel_file" in request.FILES:
            excel_file = request.FILES["excel_file"]
            print(f"Uploaded File Name: {excel_file.name}")
            print(f"Uploaded File Size: {excel_file.size}")

            try:
                # Determine file extension
                file_extension = excel_file.name.split('.')[-1].lower()
                if file_extension == "xlsx":
                    df = pd.read_excel(excel_file)
                else:
                    messages.error(request, "Invalid file format. Please upload an .xlsx file.")
                    return redirect('hodinput')

                # Debugging: Print DataFrame content
                print("DataFrame Loaded Successfully:")
                print(df.head())

                # Loop through each row of the DataFrame and create a new StudMetaData entry
                for _, row in df.iterrows():
                    try:
                        stud = StudMetaData(
                            REG_NO=row['REG_NO'],
                            stud_name=row['stud_name'],
                            degree=row['degree'],
                            stud_dept=row['stud_dept'],
                            year=row['year'],
                            section=row['section'],
                            gender=row['gender'],
                        )
                        stud.save()
                    except Exception as row_error:
                        print(f"Error saving row: {row}")
                        print(row_error)

                messages.success(request, "Excel data uploaded successfully!")

            except Exception as e:
                print("Error processing the file:", str(e))
                messages.error(request, f"Error processing the Excel file: {e}")
                return redirect('hodinput')

        # Handle manual entries from the form
        reg_no_list = request.POST.getlist('REG_NO[]')
        name_list = request.POST.getlist('name[]')
        degree_list = request.POST.getlist('degree[]')
        department_list = request.POST.getlist('department[]')
        year_list = request.POST.getlist('year[]')
        section_list = request.POST.getlist('section[]')
        gender_list = request.POST.getlist('gender[]')

        try:
            for reg_no, name, degree, department, year, section, gender in zip(
                reg_no_list, name_list, degree_list, department_list, year_list, section_list, gender_list
            ):
                if reg_no and name and degree and department and year and section and gender:
                    stud = StudMetaData(
                        REG_NO=reg_no,
                        stud_name=name,
                        degree=degree,
                        stud_dept=department,
                        year=year,
                        section=section,
                        gender=gender,
                    )
                    stud.save()

            messages.success(request, "Manual entries added successfully!")

        except Exception as e:
            print("Error saving manual entries:", str(e))
            messages.error(request, f"Error saving manual entries: {e}")
            return redirect('hodinput')

        return redirect('hodinput')  # Redirect back to the form after successful submission

    return render(request, 'hodinput.html')


def upload_success_view(request):
    return render(request, 'upload_success.html')

def upload_excel_2(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]
        
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(excel_file)

        # Loop through each row of the DataFrame and create a new HourTable entry
        for _, row in df.iterrows():
            subs = HourTable(
                at_year=row['year'],
                at_dept=row['dept'],
                at_day_order=row['dayorder'],
                sub1=row['sub1'],
                sub2=row['sub2'],
                sub3=row['sub3'],
                sub4=row['sub4'],
                sub5=row['sub5'],
                sub6=row['sub6'],
                sub7=row['sub7'],
                at_sdate=row['stdate'],
                at_edate=row['eddate'],
            )
            subs.save()
        
        return render(request, 'upload_success.html')  # Redirect to a success page or render a success message
    else:
        form = ExcelUploadForm()
    
    return render(request, 'upload_excel_2.html', {'form': form})


def logout_view(request):
    # Clear session
    request.session.flush()
    # Redirect to login page
    return HttpResponseRedirect('/login/')  # Adjust URL to your login page
