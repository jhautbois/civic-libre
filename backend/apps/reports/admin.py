from django.contrib import admin

from .models import Category, Department, Report, ReportPhoto


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "notification_email"]
    filter_horizontal = ["members"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "department", "is_active"]
    list_filter = ["department", "is_active"]
    prepopulated_fields = {"code": ["name"]}


class ReportPhotoInline(admin.TabularInline):
    model = ReportPhoto
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Consultation d'appoint : le traitement quotidien passe par
    /gestion (lot 4), pas par l'admin."""

    list_display = ["reference", "category", "status", "publication_state", "created_at"]
    list_filter = ["status", "publication_state", "category"]
    search_fields = ["reference", "description", "address"]
    readonly_fields = ["reference", "tracking_token", "created_ip", "created_user_agent"]
    inlines = [ReportPhotoInline]
