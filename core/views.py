import csv
from datetime import date
from decimal import Decimal
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Avg
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from .models import *
from .forms import *
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell

def staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))

@login_required
def dashboard(request):
    today=timezone.localdate()
    total_students=Student.objects.count()
    today_qs=Attendance.objects.filter(date=today)
    total_today=today_qs.count()
    present_today=today_qs.filter(status='P').count()
    overall=Attendance.objects.aggregate(total=Count('id'),present=Count('id',filter=Q(status='P'))) 
    overall_pct=round((overall['present']/overall['total']*100),1) if overall['total'] else 0
    below=[]
    for s in Student.objects.all():
        records=s.attendance_records.all()
        n=records.count()
        p=records.filter(status='P').count()
        pct=(p/n*100) if n else None
        if pct is not None and pct<75: below.append({'student':s,'percentage':round(pct,1)})
    avg=StudentMark.objects.aggregate(v=Avg('obtained_marks'))['v'] or 0
    context={'total_students':total_students,'total_faculty':Faculty.objects.count(),
      'total_departments':Department.objects.count(),'total_subjects':Subject.objects.count(),
      'today_pct':round(present_today/total_today*100,1) if total_today else 0,
      'overall_pct':overall_pct,'below_count':len(below),'exam_count':Examination.objects.count(),
      'average_marks':round(float(avg),2),'below_students':below[:8]}
    return render(request,'core/dashboard.html',context)

@login_required
def student_list(request):
    qs=Student.objects.select_related('department','academic_year','semester')
    q=request.GET.get('q','').strip()
    if q: qs=qs.filter(Q(roll_number__icontains=q)|Q(full_name__icontains=q)|Q(student_id__icontains=q))
    for field in ['department','academic_year','semester','section']:
        val=request.GET.get(field)
        if val: qs=qs.filter(**{field+'__'+('id' if field!='section' else 'iexact'):val}) if field!='section' else qs.filter(section__iexact=val)
    return render(request,'core/student_list.html',{'students':qs,'departments':Department.objects.all()})

@login_required
def student_create(request):
    form=StudentForm(request.POST or None,request.FILES or None)
    if form.is_valid(): form.save(); messages.success(request,'Student added successfully.'); return redirect('student_list')
    return render(request,'core/form.html',{'form':form,'title':'Add Student'})

@login_required
def student_update(request,pk):
    obj=get_object_or_404(Student,pk=pk); form=StudentForm(request.POST or None,request.FILES or None,instance=obj)
    if form.is_valid(): form.save(); messages.success(request,'Student updated.'); return redirect('student_profile',pk=pk)
    return render(request,'core/form.html',{'form':form,'title':'Edit Student'})

@login_required
@require_POST
def student_delete(request,pk):
    get_object_or_404(Student,pk=pk).delete(); messages.success(request,'Student deleted.'); return redirect('student_list')

@login_required
def student_profile(request,pk):
    student=get_object_or_404(Student,pk=pk)
    records=student.attendance_records.select_related('subject').order_by('-date')
    total=records.count(); present=records.filter(status='P').count()
    pct=round(present/total*100,1) if total else 0
    marks=student.marks.select_related('subject','examination').order_by('-examination__date')
    return render(request,'core/student_profile.html',{'student':student,'attendance':records[:30],'marks':marks,'total':total,'present':present,'percentage':pct})

@login_required
def attendance_list(request):
    qs=Attendance.objects.select_related('student','subject','subject__department').all()
    for field in ['subject','date','status']:
        value=request.GET.get(field)
        if value: qs=qs.filter(**{field:value})
    return render(request,'core/attendance_list.html',{'records':qs[:500],'subjects':Subject.objects.all()})

@login_required
def attendance_mark(request):
    form=AttendanceForm(request.POST or None)
    if form.is_valid():
        obj=form.save()
        messages.success(request,'Attendance saved.')
        return redirect('attendance_list')
    return render(request,'core/form.html',{'form':form,'title':'Mark / Update Attendance'})


@login_required
def attendance_bulk(request):
    """Mark or update attendance for all students in a selected section."""
    departments = Department.objects.all()
    academic_years = AcademicYear.objects.all()
    semesters = Semester.objects.all()
    sections = Student.objects.exclude(section='').values_list('section', flat=True).distinct().order_by('section')
    subjects = Subject.objects.select_related('department', 'semester').all()
    source = request.POST if request.method == 'POST' else request.GET
    filters = {
        'department': source.get('department', ''),
        'academic_year': source.get('academic_year', ''),
        'semester': source.get('semester', ''),
        'section': source.get('section', ''),
        'subject': source.get('subject', ''),
        'date': source.get('date', timezone.localdate().isoformat()),
    }
    students = Student.objects.select_related('department', 'academic_year', 'semester').all()
    if filters['department']: students = students.filter(department_id=filters['department'])
    if filters['academic_year']: students = students.filter(academic_year_id=filters['academic_year'])
    if filters['semester']: students = students.filter(semester_id=filters['semester'])
    if filters['section']: students = students.filter(section__iexact=filters['section'])
    students = students.order_by('roll_number')
    roster_ready = bool(filters['section'] and filters['subject'] and filters['date'])
    selected_subject = None
    if roster_ready:
        selected_subject = get_object_or_404(Subject, pk=filters['subject'])
        if filters['department'] and selected_subject.department_id != int(filters['department']):
            messages.error(request, 'Choose a subject from the selected department.')
            roster_ready = False

    if request.method == 'POST' and 'save_attendance' in request.POST:
        if not roster_ready:
            messages.error(request, 'Select a section, subject and date before saving.')
        else:
            try:
                attendance_date = date.fromisoformat(filters['date'])
            except (TypeError, ValueError):
                attendance_date = None
            if not attendance_date:
                messages.error(request, 'Enter a valid attendance date.')
            else:
                roster = list(students)
                submitted_ids = set(request.POST.getlist('student_ids'))
                valid_ids = {str(student.pk) for student in roster}
                allowed_statuses = {choice[0] for choice in Attendance.STATUS}
                if submitted_ids != valid_ids:
                    messages.error(request, 'Student list changed. Reload the page and try again.')
                elif any(request.POST.get('status_' + sid) not in allowed_statuses for sid in submitted_ids):
                    messages.error(request, 'One or more attendance statuses are invalid.')
                else:
                    with transaction.atomic():
                        for student in roster:
                            Attendance.objects.update_or_create(
                                student=student, subject=selected_subject, date=attendance_date,
                                defaults={'status': request.POST.get('status_' + str(student.pk))}
                            )
                    messages.success(request, f'Attendance saved for {len(roster)} students in section {filters["section"]}.')
                    return redirect(
                        f"{request.path}?department={filters['department']}&academic_year={filters['academic_year']}"
                        f"&semester={filters['semester']}&section={filters['section']}"
                        f"&subject={filters['subject']}&date={filters['date']}"
                    )

    existing = {}
    if roster_ready:
        existing = {str(r.student_id): r.status for r in Attendance.objects.filter(
            student__in=students, subject=selected_subject, date=filters['date']
        )}
        for student in students:
            student.bulk_status = existing.get(str(student.pk), 'P')
    return render(request, 'core/attendance_bulk.html', {
        'departments': departments, 'academic_years': academic_years, 'semesters': semesters,
        'sections': sections, 'subjects': subjects, 'students': students if roster_ready else [],
        'filters': filters, 'selected_subject': selected_subject, 'roster_ready': roster_ready,
        'existing': existing, 'status_choices': Attendance.STATUS,
    })


@login_required
def attendance_reports(request):
    qs=Attendance.objects.select_related('student','subject','student__department')
    start=request.GET.get('from_date'); end=request.GET.get('to_date')
    for key in ['subject','student__department_id','student__semester_id','student__section','student__roll_number']:
        val=request.GET.get(key.replace('__','_'))
        if val: qs=qs.filter(**{key:val})
    if start: qs=qs.filter(date__gte=start)
    if end: qs=qs.filter(date__lte=end)
    groups={}
    for a in qs:
        key=(a.student_id,a.subject_id)
        if key not in groups: groups[key]={'student':a.student,'subject':a.subject,'total':0,'present':0,'absent':0,'od':0}
        g=groups[key]; g['total']+=1
        g[{'P':'present','A':'absent','OD':'od'}[a.status]]+=1
    rows=[]
    for g in groups.values():
        g['percentage']=round(g['present']/g['total']*100,1) if g['total'] else 0
        g['status']='Excellent' if g['percentage']>=90 else ('Good' if g['percentage']>=75 else 'Shortage')
        rows.append(g)
    rows.sort(key=lambda x:x['student'].roll_number)
    return render(request,'core/attendance_reports.html',{'rows':rows,'subjects':Subject.objects.all(),'departments':Department.objects.all(),'filters':request.GET})

@login_required
def marks_list(request):
    qs=StudentMark.objects.select_related('student','subject','examination')
    if request.GET.get('examination'): qs=qs.filter(examination_id=request.GET['examination'])
    return render(request,'core/marks_list.html',{'marks':qs,'examinations':Examination.objects.all()})

@login_required
def mark_create(request):
    form=StudentMarkForm(request.POST or None)
    if form.is_valid():
        obj=form.save(commit=False)
        if obj.obtained_marks>obj.max_marks:
            form.add_error('obtained_marks','Obtained marks cannot exceed maximum marks.')
        else: obj.save(); messages.success(request,'Marks saved.'); return redirect('marks_list')
    return render(request,'core/form.html',{'form':form,'title':'Enter Student Marks'})

@login_required
def examination_create(request):
    form=ExaminationForm(request.POST or None)
    if form.is_valid(): form.save(); messages.success(request,'Examination created.'); return redirect('marks_list')
    return render(request,'core/form.html',{'form':form,'title':'Create Examination'})

@login_required
def export_students(request):
    qs=Student.objects.select_related('department','academic_year','semester')
    return export_xlsx('Students','Student Information',['Student ID','Roll Number','Name','Email','Mobile','Department','Course','Year','Semester','Section'],
      ([s.student_id,s.roll_number,s.full_name,s.email,s.mobile,str(s.department or ''),s.course,str(s.academic_year or ''),str(s.semester or ''),s.section] for s in qs),'college_students.xlsx')

@login_required
def export_attendance(request):
    qs=Attendance.objects.select_related('student','subject','student__department')
    start=request.GET.get('from_date'); end=request.GET.get('to_date')
    if start: qs=qs.filter(date__gte=start)
    if end: qs=qs.filter(date__lte=end)
    if request.GET.get('subject'): qs=qs.filter(subject_id=request.GET['subject'])
    rows=[]
    for a in qs:
        rows.append([a.date,a.student.roll_number,a.student.full_name,str(a.student.department or ''),a.subject.code,a.subject.name,a.status])
    return export_xlsx('Attendance','Attendance Report',['Date','Roll Number','Student Name','Department','Subject Code','Subject','Status'],rows,'college_attendance_report.xlsx')

@login_required
def export_marks(request):
    qs=StudentMark.objects.select_related('student','subject','examination')
    rows=[]
    for m in qs:
        rows.append([m.student.roll_number,m.student.full_name,m.subject.name,m.examination.name,float(m.max_marks),float(m.obtained_marks),round(float(m.percentage),2),m.result_status])
    return export_xlsx('Marks','Student Marks Report',['Roll Number','Student Name','Subject','Examination','Maximum Marks','Obtained Marks','Percentage','Result'],rows,'college_marks_report.xlsx')

@login_required
def export_student(request,pk):
    s=get_object_or_404(Student,pk=pk)
    rows=[[s.student_id,s.roll_number,s.full_name,s.email,s.mobile,str(s.department or ''),s.course,str(s.academic_year or ''),str(s.semester or ''),s.section]]
    return export_xlsx('Student','Student Profile',['Student ID','Roll Number','Name','Email','Mobile','Department','Course','Year','Semester','Section'],rows,f'{s.roll_number}_profile.xlsx')

def export_xlsx(sheet_name,title,headers,rows,filename):
    wb=Workbook(); ws=wb.active; ws.title=sheet_name[:31]
    ws.append([title]); ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(headers))
    ws['A1'].font=Font(bold=True,size=15,color='FFFFFF'); ws['A1'].fill=PatternFill('solid',fgColor='17365D')
    ws.append([f'Generated: {timezone.localtime():%d-%m-%Y %H:%M}'])
    ws.append(headers)
    for cell in ws[3]:
        cell.font=Font(bold=True,color='FFFFFF'); cell.fill=PatternFill('solid',fgColor='2874A6')
        cell.alignment=Alignment(horizontal='center')
    thin=Side(style='thin',color='D5D8DC')
    for row in rows:
        ws.append(list(row))
    for row in ws.iter_rows(min_row=3):
        for c in row: c.border=Border(bottom=thin)
    ws.freeze_panes='A4'; ws.auto_filter.ref=ws.dimensions
    # Determine widths by column index. Merged ranges contain MergedCell
    # placeholders, which do not expose column_letter or writable styles.
    for col_idx, col in enumerate(ws.iter_cols(min_col=1, max_col=ws.max_column), start=1):
        letter = get_column_letter(col_idx)
        values = [
            len(str(cell.value or ''))
            for cell in col
            if not isinstance(cell, MergedCell)
        ]
        content_width = max(values, default=0) + 2
        ws.column_dimensions[letter].width = min(max(content_width, 12), 34)
    response=HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition']=f'attachment; filename="{filename}"'
    wb.save(response); return response


@login_required
def bulk_marks(request):
    """Enter or update marks for every student in a selected section."""
    departments = Department.objects.all()
    academic_years = AcademicYear.objects.all()
    semesters = Semester.objects.all()
    sections = Student.objects.exclude(section='').values_list('section', flat=True).distinct().order_by('section')
    subjects = Subject.objects.select_related('department', 'semester').all()
    examinations = Examination.objects.select_related('academic_year', 'semester').all()
    source = request.POST if request.method == 'POST' else request.GET
    filters = {
        'department': source.get('department', ''),
        'academic_year': source.get('academic_year', ''),
        'semester': source.get('semester', ''),
        'section': source.get('section', ''),
        'subject': source.get('subject', ''),
        'examination': source.get('examination', ''),
        'max_marks': source.get('max_marks', ''),
    }

    students = Student.objects.select_related('department', 'academic_year', 'semester').all()
    if filters['department']:
        students = students.filter(department_id=filters['department'])
    if filters['academic_year']:
        students = students.filter(academic_year_id=filters['academic_year'])
    if filters['semester']:
        students = students.filter(semester_id=filters['semester'])
    if filters['section']:
        students = students.filter(section__iexact=filters['section'])
    students = students.order_by('roll_number')

    roster_ready = bool(filters['section'] and filters['subject'] and filters['examination'])
    selected_subject = None
    selected_examination = None
    if roster_ready:
        selected_subject = get_object_or_404(Subject, pk=filters['subject'])
        selected_examination = get_object_or_404(Examination, pk=filters['examination'])
        if filters['department'] and selected_subject.department_id != int(filters['department']):
            messages.error(request, 'Choose a subject from the selected department.')
            roster_ready = False
        if filters['semester'] and selected_subject.semester_id and selected_subject.semester_id != int(filters['semester']):
            messages.error(request, 'Choose a subject for the selected semester.')
            roster_ready = False
        if selected_examination.semester_id and filters['semester'] and selected_examination.semester_id != int(filters['semester']):
            messages.error(request, 'Choose an examination for the selected semester.')
            roster_ready = False
        if selected_examination.academic_year_id and filters['academic_year'] and selected_examination.academic_year_id != int(filters['academic_year']):
            messages.error(request, 'Choose an examination for the selected academic year.')
            roster_ready = False

    existing = {}
    default_max = filters['max_marks']
    if roster_ready:
        records = StudentMark.objects.filter(
            student__in=students, subject=selected_subject, examination=selected_examination
        )
        existing = {str(record.student_id): record for record in records}
        if not default_max and existing:
            default_max = str(next(iter(existing.values())).max_marks)
        for student in students:
            record = existing.get(str(student.pk))
            student.bulk_obtained = str(record.obtained_marks) if record else ''

    if request.method == 'POST' and 'save_bulk_marks' in request.POST:
        if not roster_ready:
            messages.error(request, 'Select a section, subject and examination before saving.')
        else:
            from decimal import InvalidOperation
            try:
                max_marks = Decimal(request.POST.get('max_marks', '').strip())
                if not max_marks.is_finite() or max_marks <= 0:
                    raise InvalidOperation
            except (InvalidOperation, AttributeError):
                messages.error(request, 'Enter a valid maximum mark greater than zero.')
            else:
                roster = list(students)
                submitted_ids = set(request.POST.getlist('student_ids'))
                valid_ids = {str(student.pk) for student in roster}
                parsed = {}
                error = None
                if submitted_ids != valid_ids:
                    error = 'Student list changed. Reload the page and try again.'
                else:
                    for student in roster:
                        raw = request.POST.get('marks_' + str(student.pk), '').strip()
                        if raw == '':
                            error = f'Enter marks for {student.roll_number} - {student.full_name}.'
                            break
                        try:
                            value = Decimal(raw)
                            if not value.is_finite() or value < 0 or value > max_marks:
                                raise InvalidOperation
                            parsed[student.pk] = value
                        except (InvalidOperation, AttributeError):
                            error = f'Invalid marks for {student.roll_number}. Marks must be between 0 and {max_marks}.'
                            break
                if error:
                    messages.error(request, error)
                else:
                    with transaction.atomic():
                        for student in roster:
                            StudentMark.objects.update_or_create(
                                student=student, subject=selected_subject, examination=selected_examination,
                                defaults={'max_marks': max_marks, 'obtained_marks': parsed[student.pk]}
                            )
                    messages.success(request, f'Marks saved for {len(roster)} students in section {filters["section"]}.')
                    return redirect(
                        f"{request.path}?department={filters['department']}&academic_year={filters['academic_year']}"
                        f"&semester={filters['semester']}&section={filters['section']}"
                        f"&subject={filters['subject']}&examination={filters['examination']}&max_marks={max_marks}"
                    )

    return render(request, 'core/marks_bulk.html', {
        'departments': departments, 'academic_years': academic_years, 'semesters': semesters,
        'sections': sections, 'subjects': subjects, 'examinations': examinations,
        'students': students if roster_ready else [], 'filters': filters,
        'selected_subject': selected_subject, 'selected_examination': selected_examination,
        'roster_ready': roster_ready, 'existing': existing, 'default_max': default_max,
    })
