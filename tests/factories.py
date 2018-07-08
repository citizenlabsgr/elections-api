import factory

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


class PollFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Poll

    county = factory.SubFactory(CountyFactory)
    jurisdiction = factory.SubFactory(JurisdictionFactory)
    ward_number = factory.Sequence(lambda n: n + 1)
    precinct_number = factory.Sequence(lambda n: n + 1)
