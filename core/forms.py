from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import ClassSession, TeacherUnavailability
from .models import ClassRoom
from .models import Student
from .models import Holiday
from accounts.models import User


class TeacherCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'TEACHER'
        if commit:
            user.save()
        return user

class TeacherUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'classroom', 'active']


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = '__all__'

    def clean_name(self):
        name = self.cleaned_data['name']
        if ClassRoom.objects.filter(name=name).exists():
            raise forms.ValidationError("Já existe uma turma com este nome.")
        return name


class ClassSessionForm(forms.ModelForm):
    class Meta:
        model = ClassSession
        fields = ['classroom', 'date', 'time', 'teacher', 'substitute_teacher', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        teachers = User.objects.filter(role='TEACHER')
        self.fields['teacher'].queryset = teachers
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['substitute_teacher'].queryset = teachers

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        teacher = cleaned_data.get('teacher')
        classroom = cleaned_data.get('classroom')

        if teacher and date and time:
            conflict_teacher = ClassSession.objects.filter(
                teacher=teacher,
                date=date,
                time=time
            )
            if self.instance.pk:
                conflict_teacher = conflict_teacher.exclude(pk=self.instance.pk)
            if conflict_teacher.exists():
                self.add_error('teacher', f'O professor {teacher.get_full_name()} já possui outra aula neste horário.')

            # Validação de indisponibilidade
        if teacher and date:
            from .models import TeacherUnavailability
            unavailability = TeacherUnavailability.objects.filter(
                teacher=teacher,
                start_date__lte=date,
                end_date__gte=date
            )
            if unavailability.exists():
                self.add_error('teacher', f"O professor {teacher.get_full_name()} está indisponível neste dia.")


        if classroom and date and time:
            conflict_classroom = ClassSession.objects.filter(
                classroom=classroom,
                date=date,
                time=time
            )
            if self.instance.pk:
                conflict_classroom = conflict_classroom.exclude(pk=self.instance.pk)
            if conflict_classroom.exists():
                self.add_error('classroom', f'A turma {classroom.name} já possui uma aula neste horário.')

        return cleaned_data


class TeacherUnavailabilityForm(forms.ModelForm):
    class Meta:
        model = TeacherUnavailability
        fields = ['teacher', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.TextInput(attrs={'placeholder': 'Ex: férias, licença médica...'})
        }
