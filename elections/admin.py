from django.contrib import admin

from . import models


@admin.register(models.DistrictCategory)
class DistrictCategoryAdmin(admin.ModelAdmin):

    search_fields = ["name"]

    list_display = ["id", "name", "created", "modified"]


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):

    search_fields = ["name"]

    list_filter = ["category"]

    list_display = ["id", "name", "category", "created", "modified"]
