# pylint: disable=unused-argument

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from . import models


class DefaultFiltersMixin(admin.ModelAdmin):
    def changelist_view(self, request, *args, **kwargs):
        default_filters = getattr(self, "default_filters", [])
        query_string = request.META["QUERY_STRING"]
        http_referer = request.META.get("HTTP_REFERER", "")
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
                    mvic_election_id=active_election.mvic_id,
                )
                for f in default_filters
            ]
            return redirect(request.path + "?" + "&".join(params))
        return super().changelist_view(request, *args, **kwargs)


@admin.register(models.DistrictCategory)
class DistrictCategoryAdmin(admin.ModelAdmin):

    search_fields = ["name"]

    list_filter = ["described", "rank"]

    list_display = [
        "id",
        "name",
        "display_name",
        "description",
        "rank",
        "modified",
    ]

    def display_name(self, category: models.DistrictCategory) -> str:
        return str(category)


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):

    search_fields = ["name"]

    list_filter = ["category"]

    list_display = ["id", "category", "name", "population", "modified"]

    ordering = ["category", "name"]


def delete_invalid_ballot_websites(modeladmin, request, queryset):
    count = 0
    for election in queryset:
        websites = models.BallotWebsite.objects.filter(
            mvic_election_id=election.mvic_id, valid=False
        )
        count += websites.delete()[0]
    messages.info(request, f"Deleted {count} invalid ballot website(s)")


@admin.register(models.Election)
class ElectionAdmin(admin.ModelAdmin):

    search_fields = ["name", "mvic_id"]

    list_filter = ["active"]

    list_display = [
        "id",
        "name",
        "mvic_id",
        "date",
        "active",
        "reference_url",
        "modified",
    ]

    ordering = ["-date"]

    actions = [delete_invalid_ballot_websites]


@admin.register(models.Precinct)
class PrecinctAdmin(admin.ModelAdmin):

    search_fields = ["county__name", "jurisdiction__name", "ward", "number"]

    list_display = ["id", "county", "jurisdiction", "ward", "number", "modified"]


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

    search_fields = ["mvic_election_id", "mvic_precinct_id", "mvic_html"]

    list_filter = ["mvic_election_id", "fetched", "valid", "parsed"]
    default_filters = [
        "mvic_election_id={mvic_election_id}",
        "fetched__exact=1",
        "valid__exact=1",
    ]

    list_display = [
        "id",
        "Link",
        "fetched",
        "last_fetch",
        "valid",
        "last_validate",
        "data_count",
        "last_scrape",
        "Ballot",
        "last_convert",
        "parsed",
        "last_parse",
    ]

    ordering = ["-last_fetch"]

    readonly_fields = [
        "Link",
        "fetched",
        "last_fetch",
        "valid",
        "last_validate",
        "data",
        "data_count",
        "last_scrape",
        "Ballot",
        "last_convert",
        "parsed",
        "last_parse",
    ]

    def Link(self, website: models.BallotWebsite):
        return format_html(
            "<a href={url!r}>MVIC: election={eid} precinct={pid}</a>",
            url=website.mvic_url,
            eid=website.mvic_election_id,
            pid=website.mvic_precinct_id,
        )

    def Ballot(self, website: models.BallotWebsite):
        if website.ballot:
            return format_html(
                '<a href={url!r} target="_blank">API: election={eid} precinct={pid}</a>',
                url=reverse("admin:elections_ballot_change", args=[website.ballot.id]),
                eid=website.ballot.election.id,
                pid=website.ballot.precinct.id,
            )
        return None

    actions = [scrape_selected_ballots, parse_selected_ballots]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("ballot__election", "ballot__precinct")


class PrecinctCountyListFilter(admin.SimpleListFilter):
    title = "County"
    parameter_name = "precinct__county"

    def lookups(self, request, model_admin):
        queryset = (
            model_admin.model.objects.filter(precinct__county__category__name="County")
            .select_related("precinct", "precinct__county")
            .order_by("precinct__county__name")
            .distinct("precinct__county__name")
        )
        return [(o.precinct.county.pk, o.precinct.county.name) for o in queryset]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(precinct__county=self.value())
        return queryset


class PrecinctJurisdictionListFilter(admin.SimpleListFilter):
    title = "Jurisdiction"
    parameter_name = "precinct__jurisdiction"

    def lookups(self, request, model_admin):
        queryset = (
            model_admin.model.objects.filter(
                precinct__jurisdiction__category__name="Jurisdiction"
            )
            .select_related("precinct", "precinct__jurisdiction")
            .order_by("precinct__jurisdiction__name")
            .distinct("precinct__jurisdiction__name")
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
        "website__mvic_election_id",
        "website__mvic_precinct_id",
        "precinct__county__name",
        "precinct__jurisdiction__name",
        "precinct__ward",
        "precinct__number",
    ]

    list_filter = [
        "election",
        PrecinctCountyListFilter,
        PrecinctJurisdictionListFilter,
    ]
    default_filters = ["election__id__exact={election_id}"]

    list_display = [
        "id",
        "Election",
        "Precinct",
        "Website",
        "modified",
    ]

    ordering = ["-modified"]

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

    readonly_fields = ("election", "precinct", "website")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "election",
            "precinct",
            "precinct__county",
            "precinct__jurisdiction",
            "website",
        )


@admin.register(models.Party)
class PartyAdmin(admin.ModelAdmin):

    search_fields = ["name"]

    list_display = ["id", "name", "Color"]

    ordering = ["name"]

    def Color(self, obj):
        return format_html(
            '<div style="background-color: {color};'
            ' padding: 10px; border: 1px solid black;">',
            color=obj.color,
        )

    readonly_fields = (
        "name",
        "Color",
    )


@admin.register(models.Proposal)
class ProposalAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ["name", "description", "reference_url"]

    list_filter = ["election"]
    default_filters = ["election__id__exact={election_id}"]

    list_display = [
        "id",
        "name",
        "description",
        "district",
        "election",
        "reference_url",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("district", "election")

    exclude = ["precincts"]


@admin.register(models.Position)
class PositionAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ["name", "description", "reference_url"]

    list_filter = [
        "election",
        "section",
        "district__category",
        "district",
        "name",
        "described",
        "term",
        "seats",
    ]
    default_filters = ["election__id__exact={election_id}"]

    list_display = [
        "id",
        "name",
        "description",
        "district",
        "election",
        "section",
        "term",
        "seats",
        "reference_url",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("district", "election")

    exclude = ["precincts"]


@admin.register(models.Candidate)
class CandidateAdmin(DefaultFiltersMixin, admin.ModelAdmin):

    search_fields = ["name", "position__name", "description", "reference_url"]

    list_filter = ["position__election", "party", "position"]
    default_filters = ["position__election__id__exact={election_id}"]

    list_display = [
        "id",
        "name",
        "party",
        "position",
        "description",
        "reference_url",
        "District",
        "Election",
        "modified",
    ]

    def District(self, obj):
        return obj.position.district

    def Election(self, obj):
        return obj.position.election

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "party", "position", "position__election", "position__district"
        )
