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


class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Election
        fields = ['url', 'id', 'name', 'date', 'active', 'reference_url']


class PrecinctSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Precinct
        fields = ['url', 'id', 'county', 'jurisdiction', 'ward', 'precinct']

    county = serializers.CharField()
    jurisdiction = serializers.CharField()
    ward = fields.NullCharField()
    precinct = fields.NullCharField()


class BallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Ballot
        fields = ['url', 'id', 'election', 'precinct', 'mi_sos_url']

    election = ElectionSerializer()
    precinct = PrecinctSerializer()


class RegistrationStatusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.RegistrationStatus
        fields = ['registered', 'precinct', 'districts']

    precinct = PrecinctSerializer()
    districts = DistrictSerializer(many=True)
