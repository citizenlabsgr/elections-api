# pylint: disable=no-self-use

from django.contrib import admin
from django.shortcuts import redirect, reverse
from django.utils.html import format_html

from . import models


class DefaultFiltersMixin(admin.ModelAdmin):
    def changelist_view(self, request, *args, **kwargs):
        default_filters = getattr(self, 'default_filters', [])
        query_string = request.META['QUERY_STRING']
        http_referer = request.META.get('HTTP_REFERER', "")
        if all([default_filters, not query_string, request.path not in http_referer]):
            election = models.Election.objects.last()
            params = [
                f.format(election_id=election.id, mi_sos_election_id=election.mi_sos_id)
                for f in default_filters
            ]
            return redirect(request.path + '?' + '&'.join(params))
        return super().changelist_view(request, *args, **kwargs)


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
class BallotWebsiteAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ['mi_sos_election_id', 'mi_sos_precinct_id', 'mi_sos_html']

    list_filter = ['mi_sos_election_id', 'source', 'fetched', 'valid', 'parsed']
    default_filters = ['mi_sos_election_id={mi_sos_election_id}', 'fetched__exact=1']

    list_display = [
        'id',
        'Link',
        'source',
        'refetch_weight',
        'fetched',
        'last_fetch',
        'valid',
        'last_fetch_with_precinct',
        'data_count',
        'last_fetch_with_ballot',
        'parsed',
        'last_parse',
        'Ballot',
    ]

    ordering = ['-last_fetch']

    readonly_fields = [
        'refetch_weight',
        'fetched',
        'last_fetch',
        'valid',
        'last_fetch_with_precinct',
        'data_count',
        'last_fetch_with_ballot',
        'parsed',
        'last_parse',
        'data',
    ]

    def Link(self, obj):
        return format_html(
            '<a href={url!r}>MI SOS: election={eid} precinct={pid}</a>',
            url=obj.mi_sos_url,
            eid=obj.mi_sos_election_id,
            pid=obj.mi_sos_precinct_id,
        )

    def Ballot(self, obj):
        if obj.ballot:
            url = reverse('admin:elections_ballot_change', args=[obj.ballot.id])
            return format_html(f"<a href={url!r}>{obj.ballot.id}</a>")
        return None


@admin.register(models.Ballot)
class BallotAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    list_filter = ['election']
    default_filters = ['election__id__exact={election_id}']

    list_display = ['id', 'election', 'precinct', 'modified']

    ordering = ['-modified']


@admin.register(models.Party)
class PartyAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = ['id', 'name', 'Color']

    ordering = ['name']

    def Color(self, obj):
        return format_html(
            '<div style="background-color: {color};'
            ' padding: 10px; border: 1px solid black;">',
            color=obj.color,
        )


@admin.register(models.Proposal)
class ProposalAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ['name', 'description', 'reference_url']

    list_filter = ['election']
    default_filters = ['election__id__exact={election_id}']

    list_display = [
        'id',
        'name',
        'description',
        'district',
        'election',
        'reference_url',
    ]


@admin.register(models.Position)
class PositionAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ['name', 'description', 'reference_url']

    list_filter = ['election', 'term', 'seats']
    default_filters = ['election__id__exact={election_id}']

    list_display = [
        'id',
        'name',
        'description',
        'district',
        'election',
        'term',
        'seats',
        'reference_url',
    ]


@admin.register(models.Candidate)
class CandidateAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ['name', 'position__name', 'description', 'reference_url']

    list_filter = ['position__election', 'party', 'position']
    default_filters = ['position__election__id__exact={election_id}']

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
