from rest_framework import serializers

from . import fields, models


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Voter
        fields = '__all__'


class DistrictCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.DistrictCategory
        fields = ['url', 'id', 'name']


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.District
        fields = ['url', 'id', 'category', 'name']

    category = serializers.CharField()


class RegistrationStatusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.RegistrationStatus
        fields = ['registered', 'districts']

    districts = DistrictSerializer(many=True)


class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Election
        fields = ['url', 'id', 'name', 'date', 'reference_url']


class PollSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Poll
        fields = [
            'url',
            'id',
            'county',
            'jurisdiction',
            'ward_number',
            'precinct_number',
        ]

    county = serializers.CharField()
    jurisdiction = serializers.CharField()
    ward_number = fields.NullIntegerField()


class BallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Ballot
        fields = ['url', 'id', 'election', 'poll', 'mi_sos_url']

    election = ElectionSerializer()
    poll = PollSerializer()
