from django.urls import path
from . import views

urlpatterns = [

    ## DASHBOARD
    path('', views.dashboard, name='dashboard'),

    # TURMAS
    path('manage/classrooms/', views.classrooms_manage, name='classrooms_manage'),
    path('manage/classrooms/create/', views.create_classroom, name='create_classroom'),
    path('manage/classrooms/edit/<int:classroom_id>/', views.edit_classroom_ajax, name='edit_classroom_ajax'),
    path('manage/classrooms/delete/<int:classroom_id>/', views.delete_classroom, name='delete_classroom'),
    path('classroom/<int:classroom_id>/schedule/', views.classroom_schedule_detail, name='classroom_schedule_detail'),

    # PROFESSORES
    path('manage/teachers/', views.teachers_manage, name='teachers_manage'),
    path('manage/teachers/create/', views.create_teacher, name='create_teacher'),
    path('edit-teacher/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('manage/teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('manage/teachers/schedule/', views.teachers_schedule_month, name='teachers_schedule_month'),
    path('teacher/<int:teacher_id>/schedule/', views.teacher_schedule_detail, name='teacher_schedule_detail'),

    # ALUNOS
    path('manage/students/', views.students_manage, name='students_manage'),
    path('manage/students/create/', views.create_student, name='create_student'),
    path('manage/students/edit/<int:student_id>/', views.edit_student_ajax, name='edit_student_ajax'),
    path('manage/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),

    # SESSÕES (AULAS)
    path('sessions/', views.sessions, name='sessions'),
    path('sessions/delete/<int:session_id>/', views.delete_session, name='delete_session'),
    path('sessions/duplicate-modal/<int:session_id>/', views.duplicate_session_modal, name='duplicate_session_modal'),
    path('sessions/export/', views.export_sessions_csv, name='export_sessions_csv'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<int:session_id>/audit/', views.session_audit_log, name='session_audit_log'),
    path('sessions/edit/<int:session_id>/', views.edit_session, name='edit_session'),


    # STATUS INLINE
    path('sessions/update-status/<int:session_id>/', views.update_session_status, name='update_session_status'),
    path('sessions/update-substitute/<int:session_id>/', views.update_session_substitute, name='update_session_substitute'),

    # INDISPONIBILIDADE DE PROFESSORES
    path('unavailabilities/', views.manage_unavailabilities, name='manage_unavailabilities'),

    # RELATÓRIO
    path('report/', views.report, name='report'),

    # AGENDAMENTO COMPLETO
    path('schedule/', views.schedule, name='schedule'),

    path('manage/students/edit/<int:student_id>/', views.edit_student_ajax, name='edit_student_ajax'),
    path('manage/students/delete/<int:student_id>/', views.delete_student_ajax, name='delete_student_ajax'),
]
