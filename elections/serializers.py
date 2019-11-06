from rest_framework import serializers

from . import fields, models


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Voter
        fields = '__all__'


class DistrictCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DistrictCategory
        fields = ['url', 'id', 'name', 'description']


class DistrictSerializer(serializers.HyperlinkedModelSerializer):

    category = serializers.CharField()

    class Meta:
        model = models.District
        fields = ['url', 'id', 'category', 'name']


class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Election
        fields = ['url', 'id', 'name', 'date', 'description', 'active', 'reference_url']


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
        fields = ['url', 'id', 'name', 'color', 'description']


class CandidateSerializer(serializers.HyperlinkedModelSerializer):
    party = PartySerializer()

    class Meta:
        model = models.Candidate
        fields = ['url', 'id', 'name', 'description', 'reference_url', 'party']


class PositionSerializer(serializers.HyperlinkedModelSerializer):

    candidates = CandidateSerializer(many=True)
    election = ElectionSerializer()
    district = DistrictSerializer()

    class Meta:
        model = models.Position
        fields = [
            'url',
            'id',
            'name',
            'description',
            'reference_url',
            'seats',
            'candidates',
            'election',
            'district',
        ]


class RegistrationStatusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.RegistrationStatus
        fields = ['registered', 'polling_location', 'precinct', 'districts']

    precinct = PrecinctSerializer()
    districts = DistrictSerializer(many=True)


class GlossarySerializer(serializers.Serializer):  # pylint: disable=abstract-method

    category = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField()
    edit_url = serializers.SerializerMethodField()

    def get_category(self, obj) -> str:  # pylint: disable=no-self-use
        categories = {
            'Party': 'parties',
            'DistrictCategory': 'districts',
            'Position': 'positions',
            'Election': 'elections',
        }
        model = obj.__class__.__name__
        return categories[model]

    def get_edit_url(self, obj):
        category = self.get_category(obj)
        name = obj.name.replace(' ', '%20')
        return f'https://github.com/citizenlabsgr/elections-api/edit/master/content/{category}/{name}.md'
