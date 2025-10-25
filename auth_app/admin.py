from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserAdmin(BaseUserAdmin):
    """
    The admin interface for your User model.
    """

    def activated(self, obj):
        return obj.is_active
    activated.boolean = True
    activated.short_description = 'Activated'
    
    list_display = ('id', 'email', 'username', 'activated', 'is_staff')
    ordering = ('id',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
