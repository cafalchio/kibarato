from django.contrib import admin
from django import forms
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.utils.html import format_html
from .models import Promotion
from .widgets import PromotionPhotoWidget


class AllPromotionsChangeList(ChangeList):
    def get_results(self, request):
        self.list_per_page = max(self.queryset.count(), 1)
        super().get_results(request)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ImageField: {"widget": PromotionPhotoWidget},
        models.DateField: {"widget": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})},
    }
    fields = ("image", "description", "price", "unit", "ends_on")
    list_display = ("description", "price", "unit")
    search_fields = ("description",)
    search_help_text = "Busque uma promoção pela descrição."
    change_list_template = "admin/promotions/promotion/change_list.html"
    actions = None
    readonly_fields = ("current_photo",)

    def get_changelist(self, request, **kwargs):
        return AllPromotionsChangeList

    class Media:
        css = {"all": ("css/promotions-admin.css?v=large-buttons-4",)}

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return ("current_photo", *fields) if obj else fields

    @admin.display(description="Foto atual")
    def current_photo(self, obj):
        if not obj.image:
            return "Sem foto"
        return format_html('<img class="promotion-current-photo" src="{}" alt="{}">', obj.image.url, obj.description)

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {
            **(extra_context or {}),
            "title": "Promoções atuais",
            "has_change_permission": self.has_change_permission(request),
            "has_view_permission": self.has_view_permission(request),
            "has_delete_permission": self.has_delete_permission(request),
        })
