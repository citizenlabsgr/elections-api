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
    precinct = factory.Sequence(lambda n: str(n + 1))

    mi_sos_id = 1111


class ElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Election

    date = pendulum.parse('2018-08-07', tz='America/Detroit')
    active = True
    mi_sos_id = 2222


class BallotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Ballot

    election = factory.SubFactory(ElectionFactory)
    precinct = factory.SubFactory(PrecinctFactory)
