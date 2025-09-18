import datetime
from django.shortcuts import render, get_object_or_404

from core.utils import register_audit
from .models import ClassRoom, ClassSession, AttendanceRecord, SessionAuditLog, Student, TeacherUnavailability
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from .models import User
from django.contrib import messages
import calendar
from django.utils import timezone
from datetime import date, timedelta
from .forms import ClassSessionForm, TeacherUnavailabilityForm
from .forms import ClassRoomForm
from .forms import StudentForm
from .forms import TeacherCreationForm
from .forms import TeacherUpdateForm
from django.views.decorators.http import require_http_methods

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
import csv
import json

from django.http import HttpResponse

from .utils import ajax_login_required

def is_coordinator(user):
    return user.role == 'COORDINATOR'


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')


def get_teachers_queryset():
    from core.models import User
    return User.objects.filter(role='TEACHER')


@login_required
@user_passes_test(is_coordinator)
def classroom_schedule_detail(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    
    today = timezone.now().date()
    start_week = today - datetime.timedelta(days=today.weekday())
    week = request.GET.get('week', '')

    if week:
        start_week = datetime.datetime.strptime(week, "%Y-%m-%d").date()

    week_days = [start_week + datetime.timedelta(days=i) for i in range(7)]

    sessions = ClassSession.objects.filter(
        classroom=classroom,
        date__range=(start_week, start_week + datetime.timedelta(days=6))
    ).order_by('date', 'time')

    schedule = {day: [] for day in week_days}
    for session in sessions:
        schedule[session.date].append(session)

    return render(request, 'core/classroom_schedule_detail.html', {
        'classroom': classroom,
        'week_days': week_days,
        'schedule': schedule,
        'current_week': start_week
    })


@login_required
def teacher_schedule_detail(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='TEACHER')

    # Permissão:
    if request.user.role == 'TEACHER' and request.user.id != teacher_id:
        raise PermissionDenied("Você não pode acessar a agenda de outro professor.")

    today = timezone.now().date()
    start_week = today - datetime.timedelta(days=today.weekday())
    week = request.GET.get('week', '')

    if week:
        start_week = datetime.datetime.strptime(week, "%Y-%m-%d").date()

    week_days = [start_week + datetime.timedelta(days=i) for i in range(7)]

    sessions = ClassSession.objects.filter(
        teacher=teacher,
        date__range=(start_week, start_week + datetime.timedelta(days=6))
    ).order_by('date', 'time')

    schedule = {day: [] for day in week_days}
    for session in sessions:
        schedule[session.date].append(session)

    return render(request, 'core/teacher_schedule_detail.html', {
        'teacher': teacher,
        'week_days': week_days,
        'schedule': schedule,
        'current_week': start_week
    })



@login_required
@user_passes_test(is_coordinator)
def teachers_schedule_month(request):
    today = date.today()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)

    year = int(year)
    month = int(month)

    num_days = calendar.monthrange(year, month)[1]
    days = [date(year, month, day) for day in range(1, num_days + 1)]

    teachers = User.objects.filter(role='TEACHER')
    sessions = ClassSession.objects.filter(date__year=year, date__month=month)

    schedule = {}

    for teacher in teachers:
        schedule[teacher] = {}
        for day in days:
            sessions_on_day = sessions.filter(date=day, teacher=teacher)
            if sessions_on_day.exists():
                # Pode ter mais de uma turma no dia
                classes = ", ".join([s.classroom.name for s in sessions_on_day])
                schedule[teacher][day] = classes
            else:
                schedule[teacher][day] = ""

    return render(request, 'core/teachers_schedule_month.html', {
        'days': days,
        'schedule': schedule,
        'year': year,
        'month': month,
    })


@ajax_login_required
@user_passes_test(is_coordinator)
@require_http_methods(["GET", "POST"])
def edit_teacher_ajax(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='TEACHER')
    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            row_html = render_to_string('core/partials/teacher_table_row.html', {'teacher': teacher}, request=request)
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/teacher_edit_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = TeacherUpdateForm(instance=teacher)
        form_html = render_to_string('core/partials/teacher_edit_form.html', {'form': form}, request=request)
        return JsonResponse({'form_html': form_html})


@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def delete_teacher(request, teacher_id):
    if request.method == 'POST':
        teacher = get_object_or_404(User, id=teacher_id, role='TEACHER')
        teacher.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})

@login_required
@user_passes_test(is_coordinator)
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='TEACHER')
    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Professor atualizado com sucesso!")
            return HttpResponseRedirect(reverse('teachers_manage'))
    else:
        form = TeacherUpdateForm(instance=teacher)
    return render(request, 'core/edit_teacher.html', {'form': form})



@login_required
@user_passes_test(is_coordinator)
def teachers_manage(request):
    query = request.GET.get('q')
    if query:
        teachers = User.objects.filter(role='TEACHER').filter(
            username__icontains=query
        ) | User.objects.filter(role='TEACHER').filter(
            first_name__icontains=query
        ) | User.objects.filter(role='TEACHER').filter(
            last_name__icontains=query
        )
    else:
        teachers = User.objects.filter(role='TEACHER')
    
    return render(request, 'core/teachers_manage.html', {'teachers': teachers, 'query': query})


@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def create_teacher(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            row_html = render_to_string('core/partials/teacher_table_row.html', {'teacher': teacher})
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/teacher_edit_form.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})

    elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = TeacherCreationForm()
        form_html = render_to_string('core/partials/teacher_edit_form.html', {'form': form})
        return JsonResponse({'form_html': form_html})

    return redirect('teachers_manage')



# ==================== CRUD ALUNOS COM MODAL =====================

@login_required
@user_passes_test(is_coordinator)
def students_manage(request):
    query = request.GET.get('q', '')
    students = Student.objects.select_related('classroom')

    if query:
        students = students.filter(
            full_name__icontains=query
        ) | students.filter(
            classroom__name__icontains=query
        )

    return render(request, 'core/students_manage.html', {
        'students': students,
        'query': query
    })

@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def create_student(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect('students_manage')

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            row_html = render_to_string('core/partials/student_table_row.html', {'student': student})
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/student_edit_form.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})

    else:  # GET
        form = StudentForm()
        form_html = render_to_string('core/partials/student_edit_form.html', {'form': form})
        return JsonResponse({'form_html': form_html})



@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def delete_student(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        student.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})

@login_required
@user_passes_test(is_coordinator)
def classrooms_manage(request):
    query = request.GET.get('q', '')
    classrooms = ClassRoom.objects.all()

    if query:
        classrooms = classrooms.filter(
            name__icontains=query
        )

    return render(request, 'core/classrooms_manage.html', {
        'classrooms': classrooms,
        'query': query
    })


@login_required
@user_passes_test(is_coordinator)
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('students_manage'))
    else:
        form = StudentForm(instance=student)
    return render(request, 'core/edit_student.html', {'form': form, 'student': student})


@ajax_login_required
@user_passes_test(is_coordinator)
def edit_student_ajax(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            row_html = render_to_string('core/partials/student_table_row.html', {'student': student}, request=request)
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/student_edit_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    
    else:  # GET - carregar o form no modal
        form = StudentForm(instance=student)
        form_html = render_to_string('core/partials/student_edit_form.html', {'form': form}, request=request)
        return JsonResponse({'form_html': form_html})


@ajax_login_required
@user_passes_test(is_coordinator)
@require_http_methods(["POST"])
def delete_student_ajax(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    return JsonResponse({'success': True})


@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def create_classroom(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = ClassRoomForm(request.POST)
        if form.is_valid():
            classroom = form.save()
            row_html = render_to_string('core/partials/classroom_table_row.html', {'classroom': classroom})
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/classroom_edit_form.html', {'form': form})
            return JsonResponse({'success': False, 'form_html': form_html})

    elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = ClassRoomForm()
        form_html = render_to_string('core/partials/classroom_edit_form.html', {'form': form})
        return JsonResponse({'form_html': form_html})

    return redirect('classrooms_manage')


@ajax_login_required
@user_passes_test(is_coordinator)
def edit_classroom_ajax(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)

    if request.method == 'POST':
        form = ClassRoomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            row_html = render_to_string('core/partials/classroom_table_row.html', {'classroom': classroom}, request=request)
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/classroom_edit_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = ClassRoomForm(instance=classroom)
        form_html = render_to_string('core/partials/classroom_edit_form.html', {'form': form}, request=request)
        return JsonResponse({'form_html': form_html})

    
@login_required
@user_passes_test(is_coordinator)
def edit_classroom(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    if request.method == 'POST':
        form = ClassRoomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('classrooms_manage'))
    else:
        form = ClassRoomForm(instance=classroom)

    return render(request, 'core/classroom_form.html', {
        'form': form,
        'title': 'Editar Turma'
    })


@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def delete_classroom(request, classroom_id):
    if request.method == 'POST':
        classroom = get_object_or_404(ClassRoom, id=classroom_id)
        classroom.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})

@login_required
def schedule(request):
    user = request.user

    today = datetime.date.today()
    start_week = today - datetime.timedelta(days=today.weekday())  # segunda-feira
    days = [start_week + datetime.timedelta(days=i) for i in range(7)]

    if user.role == 'TEACHER':
        sessions = ClassSession.objects.filter(
            classroom__teacher=user,
            date__range=(days[0], days[-1])
        )
    elif user.role == 'COORDINATOR':
        sessions = ClassSession.objects.filter(date__range=(days[0], days[-1]))
    else:
        sessions = ClassSession.objects.none()

    sessions_by_date = {}
    for day in days:
        sessions_by_date[day] = sessions.filter(date=day)

    return render(request, 'core/schedule.html', {
        'days': days,
        'sessions_by_date': sessions_by_date
    })
    

@login_required
def report(request):
    user = request.user

    if user.role == 'TEACHER':
        classrooms = ClassRoom.objects.filter(teacher=user)
    elif user.role == 'COORDINATOR':
        classrooms = ClassRoom.objects.all()
    else:
        classrooms = ClassRoom.objects.none()

    report_data = []

    for classroom in classrooms:
        students = Student.objects.filter(classroom=classroom)
        for student in students:
            records = AttendanceRecord.objects.filter(student=student)
            total_points = 0
            for record in records:
                total_points += (
                    record.present +
                    record.punctual +
                    record.uniform +
                    record.book +
                    record.repost
                )
            report_data.append({
                'classroom': classroom.name,
                'student': student.full_name,
                'points': total_points,
            })

    return render(request, 'core/report.html', {'report_data': report_data})


@login_required 
def sessions(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    classroom_filter = request.GET.get('classroom', '')
    teacher_filter = request.GET.get('teacher', '')

    user = request.user

    if user.role == 'TEACHER':
        sessions = ClassSession.objects.filter(classroom__in=ClassRoom.objects.filter(classsession__teacher=user))
    elif user.role == 'COORDINATOR':
        sessions = ClassSession.objects.all()
    else:
        sessions = ClassSession.objects.none()

    sessions = sessions.order_by('date', 'time')

    if query:
        sessions = sessions.filter(
            classroom__name__icontains=query
        ) | sessions.filter(
            teacher__first_name__icontains=query
        )

    if status_filter in ['SCHEDULED', 'COMPLETED', 'CANCELLED']:
        sessions = sessions.filter(status=status_filter)

    if start_date:
        sessions = sessions.filter(date__gte=start_date)

    if end_date:
        sessions = sessions.filter(date__lte=end_date)

    if classroom_filter:
        sessions = sessions.filter(classroom__id=classroom_filter)

    if teacher_filter:
        sessions = sessions.filter(teacher__id=teacher_filter)

    # Paginação
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Criamos os forms individuais para cada sessão paginada (para o modal)
    session_forms = {session.id: ClassSessionForm(instance=session) for session in page_obj}

    # Enviar também as listas de turmas e professores para os filtros
    classrooms = ClassRoom.objects.all()
    teachers = User.objects.filter(role='TEACHER')

    return render(request, 'core/sessions.html', {
        'sessions': page_obj,
        'session_forms': session_forms,  # Adicionado para o modal
        'query': query,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'classroom_filter': classroom_filter,
        'teacher_filter': teacher_filter,
        'classrooms': classrooms,
        'teachers': teachers
    })



@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def create_session(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = ClassSessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            teachers = User.objects.filter(role='TEACHER')
            row_html = render_to_string('core/partials/session_table_row.html', {
                'session': session,
                'teachers': teachers
            })
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('core/partials/create_session_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})

    elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = ClassSessionForm()
        form_html = render_to_string('core/partials/create_session_form.html', {'form': form}, request=request)
        return JsonResponse({'form_html': form_html})

    return redirect('sessions')




@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def edit_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)

    if request.method == 'POST':
        form = ClassSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            row_html = render_to_string('core/partials/session_table_row.html', {
                'session': session,
                'teachers': get_teachers_queryset()
            }, request=request)
            return JsonResponse({'success': True, 'row_html': row_html, 'id': session.id})
        else:
            form_html = render_to_string('core/partials/create_session_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})

    else:
        form = ClassSessionForm(instance=session)
        form_html = render_to_string('core/partials/create_session_form.html', {'form': form}, request=request)
        return JsonResponse({'form_html': form_html})



@login_required
@user_passes_test(is_coordinator)
@require_http_methods(["POST"])
@csrf_exempt
def update_session_status(request, session_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        status = data.get('status')
        session = get_object_or_404(ClassSession, id=session_id)
        session.status = status
        session.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
@user_passes_test(lambda u: u.role == 'COORDINATOR')
def update_session_substitute(request, session_id):
    if request.method == 'POST':
        try:
            session = ClassSession.objects.get(pk=session_id)
            substitute_id = request.POST.get('substitute_id')

            if substitute_id:
                substitute = User.objects.get(pk=substitute_id)
                session.substitute_teacher = substitute
            else:
                session.substitute_teacher = None

            session.save()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método não permitido'})

@login_required
@user_passes_test(is_coordinator)
@require_http_methods(["GET"])
def duplicate_session_modal(request, session_id):
    original_session = get_object_or_404(ClassSession, id=session_id)
    
    # Pré-preenche os dados:
    from datetime import timedelta

    initial_data = {
        'classroom': original_session.classroom,
        'teacher': original_session.teacher,
        'substitute_teacher': original_session.substitute_teacher,
        'time': original_session.time,
        'status': 'SCHEDULED',  # sempre volta para agendada
        'date': original_session.date + timedelta(days=7)
    }

    form = ClassSessionForm(initial=initial_data)
    
    form_html = render_to_string('core/partials/create_session_form.html', {'form': form}, request=request)
    return JsonResponse({'form_html': form_html})



@login_required
@user_passes_test(is_coordinator)
@require_http_methods(["POST"])
@csrf_exempt
def delete_session(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    session.delete()
    return JsonResponse({'success': True})


@login_required
@user_passes_test(is_coordinator)
def session_audit_log(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    logs = SessionAuditLog.objects.filter(session=session).order_by('-timestamp')

    return render(request, 'core/session_audit_log.html', {
        'session': session,
        'logs': logs
    })


@login_required
def classrooms(request):
    user = request.user

    if user.role == 'TEACHER':
        classrooms = ClassRoom.objects.filter(teacher=user)
    elif user.role == 'COORDINATOR':
        classrooms = ClassRoom.objects.all()
    else:
        classrooms = ClassRoom.objects.none()

    return render(request, 'core/classrooms.html', {'classrooms': classrooms})


@login_required
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    students = Student.objects.filter(classroom=classroom)
    sessions = ClassSession.objects.filter(classroom=classroom)
    return render(request, 'core/classroom_detail.html', {
        'classroom': classroom,
        'students': students,
        'sessions': sessions,
    })

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(ClassSession, pk=session_id)
    records = AttendanceRecord.objects.filter(session=session)

    if request.method == 'POST':
        for record in records:
            prefix = f"record_{record.id}_"
            record.present = bool(request.POST.get(prefix + 'present'))
            record.punctual = bool(request.POST.get(prefix + 'punctual'))
            record.uniform = bool(request.POST.get(prefix + 'uniform'))
            record.book = bool(request.POST.get(prefix + 'book'))
            record.repost = bool(request.POST.get(prefix + 'repost'))
            record.save()
        return HttpResponseRedirect(reverse('session_detail', args=[session.id]))

    return render(request, 'core/session_detail.html', {
        'session': session,
        'records': records,
    })


#=================== Exportar dados para CSV ===================
import csv
from django.http import HttpResponse

@login_required
@user_passes_test(is_coordinator)
def export_sessions_csv(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    sessions = ClassSession.objects.all().order_by('date', 'time')

    if query:
        sessions = sessions.filter(
            classroom__name__icontains=query
        ) | sessions.filter(
            teacher__first_name__icontains=query
        )

    if status_filter in ['SCHEDULED', 'COMPLETED', 'CANCELLED']:
        sessions = sessions.filter(status=status_filter)

    # Criar o arquivo CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sessoes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Hora', 'Turma', 'Professor', 'Status'])

    for session in sessions:
        writer.writerow([
            session.date.strftime('%d/%m/%Y'),
            session.time.strftime('%H:%M'),
            session.classroom.name,
            session.teacher.get_full_name() if session.teacher else 'Sem professor',
            session.get_status_display()
        ])

    return response


@login_required
@user_passes_test(is_coordinator)
def manage_unavailabilities(request):
    unavailabilities = TeacherUnavailability.objects.all().order_by('-start_date')

    if request.method == 'POST':
        form = TeacherUnavailabilityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Indisponibilidade registrada com sucesso.")
            return redirect('manage_unavailabilities')
    else:
        form = TeacherUnavailabilityForm()

    return render(request, 'core/manage_unavailabilities.html', {
        'form': form,
        'unavailabilities': unavailabilities
    })
