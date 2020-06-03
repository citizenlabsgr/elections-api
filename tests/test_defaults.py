# pylint: disable=unused-argument,unused-variable


from elections import defaults
from elections.models import District, DistrictCategory, Party


def describe_initialize_parties():
    def it_can_be_called_multiple_times(expect, db):
        defaults.initialize_parties()
        defaults.initialize_parties()

        expect(Party.objects.count()) == 9


def describe_initialize_districts():
    def it_can_be_called_multiple_times(expect, db):
        defaults.initialize_districts()
        defaults.initialize_districts()

        expect(DistrictCategory.objects.count()) == 26
        expect(District.objects.count()) == 1
