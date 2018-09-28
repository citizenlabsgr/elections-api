# pylint: disable=no-self-use

from django.contrib import admin

from . import models


@admin.register(models.DistrictCategory)
class DistrictCategoryAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = ['id', 'name', 'modified']


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_filter = ['category']

    list_display = ['id', 'category', 'name', 'population', 'modified']

    ordering = ['category', 'name']


@admin.register(models.Election)
class ElectionAdmin(admin.ModelAdmin):

    search_fields = ['name', 'mi_sos_id']

    list_filter = ['active']

    list_display = [
        'id',
        'name',
        'mi_sos_id',
        'date',
        'active',
        'reference_url',
        'modified',
    ]

    ordering = ['-date']


@admin.register(models.Precinct)
class PrecinctAdmin(admin.ModelAdmin):

    search_fields = [
        'county__name',
        'jurisdiction__name',
        'ward',
        'number',
        'mi_sos_id',
    ]

    list_display = [
        'id',
        'county',
        'jurisdiction',
        'ward',
        'number',
        'mi_sos_id',
        'modified',
    ]


@admin.register(models.BallotWebsite)
class BallotWebsiteAdmin(admin.ModelAdmin):

    search_fields = ['mi_sos_election_id', 'mi_sos_precinct_id']

    list_filter = ['valid', 'source']

    list_display = [
        'id',
        'mi_sos_election_id',
        'mi_sos_precinct_id',
        'mi_sos_url',
        'valid',
        'source',
        'table_count',
        'refetch_weight',
        'last_fetch',
        'last_fetch_with_precent',
        'last_fetch_with_ballot',
    ]

    ordering = ['-last_fetch']


@admin.register(models.Ballot)
class BallotAdmin(admin.ModelAdmin):

    list_filter = ['election']

    list_display = ['id', 'election', 'precinct', 'website', 'modified']

    ordering = ['-modified']


@admin.register(models.Party)
class PartyAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = ['id', 'name']

    ordering = ['name']


@admin.register(models.Proposal)
class ProposalAdmin(admin.ModelAdmin):

    search_fields = ['name', 'description', 'reference_url']

    list_filter = ['election']

    list_display = [
        'id',
        'name',
        'description',
        'district',
        'election',
        'reference_url',
    ]


@admin.register(models.Position)
class PositionAdmin(admin.ModelAdmin):

    search_fields = ['name', 'description', 'reference_url']

    list_filter = ['election', 'seats']

    list_display = [
        'id',
        'name',
        'description',
        'district',
        'election',
        'seats',
        'reference_url',
    ]


@admin.register(models.Candidate)
class CandidateAdmin(admin.ModelAdmin):

    search_fields = ['name', 'position__name', 'description', 'reference_url']

    list_filter = ['party', 'position', 'position__election']

    list_display = [
        'id',
        'name',
        'party',
        'position',
        'description',
        'reference_url',
        'District',
        'Election',
        'modified',
    ]

    def District(self, obj):
        return obj.position.district

    def Election(self, obj):
        return obj.position.election
