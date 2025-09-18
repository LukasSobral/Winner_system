from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ClassRoom, Student, ClassSession, AttendanceRecord
from .models import Holiday


# Personalizando o User no admin
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

admin.site.register(User, UserAdmin)
admin.site.register(ClassRoom)
admin.site.register(Student)
admin.site.register(ClassSession)
admin.site.register(AttendanceRecord)



@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'description')
    ordering = ('date',)
