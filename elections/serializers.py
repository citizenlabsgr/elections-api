# pylint: disable=no-self-use

import pendulum
from rest_framework import serializers

from . import fields, models


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Voter
        fields = '__all__'


class DistrictCategorySerializer(serializers.HyperlinkedModelSerializer):

    description_edit_url = serializers.SerializerMethodField()

    class Meta:
        model = models.DistrictCategory
        fields = ['url', 'id', 'name', 'description', 'description_edit_url']

    def get_description_edit_url(self, instance):
        category = 'districts'
        name = instance.name.replace(' ', '%20')
        return f'https://github.com/citizenlabsgr/elections-api/edit/master/content/{category}/{name}.md'


class DistrictSerializer(serializers.HyperlinkedModelSerializer):

    category = serializers.CharField()

    class Meta:
        model = models.District
        fields = ['url', 'id', 'category', 'name']


class ElectionSerializer(serializers.ModelSerializer):

    date_humanized = serializers.SerializerMethodField()
    description_edit_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Election
        fields = [
            'url',
            'id',
            'name',
            'date',
            'date_humanized',
            'description',
            'description_edit_url',
            'active',
            'reference_url',
        ]

    def get_date_humanized(self, instance) -> str:
        dt = pendulum.datetime(
            instance.date.year, instance.date.month, instance.date.day
        )
        return dt.format('dddd, MMMM Do')

    def get_description_edit_url(self, instance) -> str:
        category = 'elections'
        name = instance.name.replace(' ', '%20')
        return f'https://github.com/citizenlabsgr/elections-api/edit/master/content/{category}/{name}.md'


class PrecinctSerializer(serializers.HyperlinkedModelSerializer):

    county = serializers.CharField()
    jurisdiction = serializers.CharField()
    ward = fields.NullCharField()
    number = fields.NullCharField()

    class Meta:
        model = models.Precinct
        fields = ['url', 'id', 'county', 'jurisdiction', 'ward', 'number']


class BallotSerializer(serializers.HyperlinkedModelSerializer):

    election = ElectionSerializer()
    precinct = PrecinctSerializer()

    class Meta:
        model = models.Ballot
        fields = ['url', 'id', 'election', 'precinct', 'mi_sos_url']


class ProposalSerializer(serializers.HyperlinkedModelSerializer):

    election = ElectionSerializer()
    district = DistrictSerializer()

    class Meta:
        model = models.Proposal
        fields = [
            'url',
            'id',
            'name',
            'description',
            'reference_url',
            'election',
            'district',
        ]


class PartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Party
        fields = ['url', 'id', 'name', 'color']


class CandidateSerializer(serializers.HyperlinkedModelSerializer):

    party = PartySerializer()

    class Meta:
        model = models.Candidate
        fields = ['url', 'id', 'name', 'description', 'reference_url', 'party']


class PositionSerializer(serializers.HyperlinkedModelSerializer):

    candidates = CandidateSerializer(many=True)
    election = ElectionSerializer()
    district = DistrictSerializer()
    description_edit_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Position
        fields = [
            'url',
            'id',
            'name',
            'description',
            'description_edit_url',
            'reference_url',
            'section',
            'seats',
            'term',
            'candidates',
            'election',
            'district',
        ]

    def get_description_edit_url(self, instance):
        category = 'positions'
        name = instance.name.replace(' ', '%20')
        return f'https://github.com/citizenlabsgr/elections-api/edit/master/content/{category}/{name}.md'


class RegistrationStatusSerializer(serializers.HyperlinkedModelSerializer):

    precinct = PrecinctSerializer()
    districts = DistrictSerializer(many=True)

    class Meta:
        model = models.RegistrationStatus
        fields = [
            'registered',
            'absentee',
            'polling_location',
            'recently_moved',
            'precinct',
            'districts',
        ]


class GlossarySerializer(serializers.Serializer):  # pylint: disable=abstract-method

    category = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField()
    edit_url = serializers.SerializerMethodField()

    def get_category(self, instance) -> str:
        categories = {
            'Party': 'parties',
            'DistrictCategory': 'districts',
            'Position': 'positions',
            'Election': 'elections',
        }
        model = instance.__class__.__name__
        return categories[model]

    def get_edit_url(self, instance):
        category = self.get_category(instance)
        name = instance.name.replace(' ', '%20')
        return f'https://github.com/citizenlabsgr/elections-api/edit/master/content/{category}/{name}.md'
