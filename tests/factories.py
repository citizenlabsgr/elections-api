import factory
import pendulum

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
    date = pendulum.parse('2018-08-07', tz='America/Detroit')
    active = True
    mi_sos_id = 2222


class BallotWebsiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BallotWebsite

    mi_sos_election_id = 2222
    mi_sos_precinct_id = 1111


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
