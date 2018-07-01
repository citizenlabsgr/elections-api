from rest_framework import serializers

from . import models


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Voter
        fields = "__all__"


class RegistrationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistrationStatus
        fields = ["registered"]


class RegionKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegionKind
        fields = ["name"]


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Region
        fields = ["kind", "name"]

    kind = serializers.CharField()
