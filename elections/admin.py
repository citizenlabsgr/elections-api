# pylint: disable=no-self-use,unused-argument

from django.contrib import admin
from django.shortcuts import redirect, reverse
from django.utils.html import format_html

from . import models


class DefaultFiltersMixin(admin.ModelAdmin):
    def changelist_view(self, request, *args, **kwargs):
        default_filters = getattr(self, 'default_filters', [])
        query_string = request.META['QUERY_STRING']
        http_referer = request.META.get('HTTP_REFERER', "")
        active_election = models.Election.objects.filter(active=True).last()
        if all(
            [
                default_filters,
                not query_string,
                request.path not in http_referer,
                active_election,
            ]
        ):
            params = [
                f.format(
                    election_id=active_election.id,
                    mi_sos_election_id=active_election.mi_sos_id,
                )
                for f in default_filters
            ]
            return redirect(request.path + '?' + '&'.join(params))
        return super().changelist_view(request, *args, **kwargs)


@admin.register(models.DistrictCategory)
class DistrictCategoryAdmin(admin.ModelAdmin):

    search_fields = ['name']

    list_display = ['id', 'name', 'display_name', 'rank', 'modified']

    def display_name(self, category: models.DistrictCategory) -> str:
        return str(category)


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

    search_fields = ['county__name', 'jurisdiction__name', 'ward', 'number']

    list_display = ['id', 'county', 'jurisdiction', 'ward', 'number', 'modified']


def scrape_selected_ballots(modeladmin, request, queryset):
    for website in queryset:
        website.fetch()
        website.validate()
        website.scrape()
        website.convert()


def parse_selected_ballots(modeladmin, request, queryset):
    for website in queryset:
        ballot = website.convert()
        ballot.parse()


@admin.register(models.BallotWebsite)
class BallotWebsiteAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ['mi_sos_election_id', 'mi_sos_precinct_id', 'mi_sos_html']

    list_filter = ['mi_sos_election_id', 'fetched', 'valid', 'parsed']
    default_filters = [
        'mi_sos_election_id={mi_sos_election_id}',
        'fetched__exact=1',
        'valid__exact=1',
    ]

    list_display = [
        'id',
        'link',
        'fetched',
        'last_fetch',
        'valid',
        'last_validate',
        'data_count',
        'last_scrape',
        'ballot',
        'last_convert',
        'parsed',
        'last_parse',
    ]

    ordering = ['-last_fetch']

    readonly_fields = [
        'fetched',
        'last_fetch',
        'valid',
        'last_validate',
        'data',
        'data_count',
        'last_scrape',
        'ballot',
        'last_convert',
        'parsed',
        'last_parse',
    ]

    def link(self, website: models.BallotWebsite):
        return format_html(
            '<a href={url!r}>MI SOS: election={eid} precinct={pid}</a>',
            url=website.mi_sos_url,
            eid=website.mi_sos_election_id,
            pid=website.mi_sos_precinct_id,
        )

    actions = [scrape_selected_ballots, parse_selected_ballots]


class PrecinctCountyListFilter(admin.SimpleListFilter):
    title = "County"
    parameter_name = 'precinct__county'

    def lookups(self, request, model_admin):
        queryset = (
            model_admin.model.objects.filter(precinct__county__category__name="County")
            .order_by('precinct__county__name')
            .distinct('precinct__county__name')
        )
        return [(o.precinct.county.pk, o.precinct.county.name) for o in queryset]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(precinct__county=self.value())
        return queryset


class PrecinctJurisdictionListFilter(admin.SimpleListFilter):
    title = "Jurisdiction"
    parameter_name = 'precinct__jurisdiction'

    def lookups(self, request, model_admin):
        queryset = (
            model_admin.model.objects.filter(
                precinct__jurisdiction__category__name="Jurisdiction"
            )
            .order_by('precinct__jurisdiction__name')
            .distinct('precinct__jurisdiction__name')
        )
        return [
            (o.precinct.jurisdiction.pk, o.precinct.jurisdiction.name) for o in queryset
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(precinct__jurisdiction=self.value())
        return queryset


@admin.register(models.Ballot)
class BallotAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = [
        'website__mi_sos_election_id',
        'website__mi_sos_precinct_id',
        'precinct__county__name',
        'precinct__jurisdiction__name',
        'precinct__ward',
        'precinct__number',
    ]

    list_filter = [
        'election',
        PrecinctCountyListFilter,
        PrecinctJurisdictionListFilter,
    ]
    default_filters = ['election__id__exact={election_id}']

    list_display = [
        'id',
        'Election',
        'Precinct',
        'Website',
        'modified',
    ]

    ordering = ['-modified']

    def Election(self, obj):
        url = reverse("admin:elections_election_change", args=[obj.election.pk])
        return format_html(
            '<a href="{href}" target="_blank">{pk}: {label}</a>',
            href=url,
            pk=obj.election.pk,
            label=obj.election,
        )

    def Precinct(self, obj):
        url = reverse("admin:elections_precinct_change", args=[obj.precinct.pk])
        return format_html(
            '<a href="{href}" target="_blank">{pk}: {label}</a>',
            href=url,
            pk=obj.precinct.pk,
            label=obj.precinct,
        )

    def Website(self, obj):
        if obj.website:
            url = reverse("admin:elections_ballotwebsite_change", args=[obj.website.pk])
            return format_html(
                '<a href="{href}" target="_blank">{pk}: {label}</a>',
                href=url,
                pk=obj.website.pk,
                label=obj.website,
            )
        return None


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

    list_filter = [
        'election',
        'section',
        'district__category',
        'district',
        'name',
        'term',
        'seats',
    ]
    default_filters = ['election__id__exact={election_id}']

    list_display = [
        'id',
        'name',
        'description',
        'district',
        'election',
        'section',
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
        'district',
        'election',
        'modified',
    ]

    def district(self, obj):
        return obj.position.district

    def election(self, obj):
        return obj.position.election
