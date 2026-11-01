import csv
from datetime import date
from decimal import Decimal
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Avg
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from .models import *
from .forms import *

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
    for col in ws.columns:
        letter=col[0].column_letter
        ws.column_dimensions[letter].width=min(max(max(len(str(c.value or '')) for c in col)+2,12),34)
    response=HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition']=f'attachment; filename="{filename}"'
    wb.save(response); return response
