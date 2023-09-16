import factory
from django.utils import timezone

from elections import models


class DistrictCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DistrictCategory


class CountyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.District

    category = factory.SubFactory(DistrictCategoryFactory, name="Country")


class JurisdictionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.District

    category = factory.SubFactory(DistrictCategoryFactory, name="Jurisdiction")


class PrecinctFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Precinct

    county = factory.SubFactory(CountyFactory)
    jurisdiction = factory.SubFactory(JurisdictionFactory)
    ward = factory.Sequence(lambda n: str(n + 1))
    number = factory.Sequence(lambda n: str(n + 1))


class ElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Election

    name = "General Election"
    date = timezone.make_aware(timezone.datetime(2018, 8, 7))
    active = True
    mvic_id = 2222


class BallotWebsiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BallotWebsite

    mvic_election_id = 2222
    mvic_precinct_id = 1111


class BallotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Ballot

    election = factory.SubFactory(ElectionFactory)
    precinct = factory.SubFactory(PrecinctFactory)

    website = factory.SubFactory(BallotWebsiteFactory)


class PositionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Position

    election = factory.SubFactory(ElectionFactory)
