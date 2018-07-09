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

    search_fields = ['name', 'mi_sos_id']

    list_filter = ['active']

    list_display = [
        'id',
        'name',
        'date',
        'active',
        'reference_url',
        'mi_sos_id',
        'created',
        'modified',
    ]


@admin.register(models.Poll)
class PollAdmin(admin.ModelAdmin):

    search_fields = [
        'county__name',
        'jurisdiction__name',
        'ward_number',
        'precinct_number',
        'precinct_letter',
        'mi_sos_id',
    ]

    list_display = [
        'id',
        'county',
        'jurisdiction',
        'ward_number',
        'precinct_number',
        'precinct_letter',
        'mi_sos_id',
        'created',
        'modified',
    ]


@admin.register(models.Ballot)
class BallotAdmin(admin.ModelAdmin):

    list_display = ['id', 'election', 'poll', 'mi_sos_url']
