from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'tipo', 'is_active')
    list_filter = ('tipo', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Dados extras', {'fields': ('tipo', 'telefone', 'data_nascimento', 'foto', 'cpf')}),
    )