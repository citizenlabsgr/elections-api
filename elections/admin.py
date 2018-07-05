from django.contrib import admin

from . import models


@admin.register(models.DistrictCategory)
class DistrictCategoryAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = ['id', 'name', 'created', 'modified']


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_filter = ['category']

    list_display = [
        'id',
        'name',
        'category',
        'population',
        'created',
        'modified',
    ]


@admin.register(models.Election)
class ElectionAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = ['id', 'name', 'mi_sos_id', 'created', 'modified']


@admin.register(models.Precinct)
class PrecinctAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = [
        'id',
        'county',
        'jurisdiction',
        'ward_number',
        'precinct_number',
        'mi_sos_id',
        'created',
        'modified',
    ]
