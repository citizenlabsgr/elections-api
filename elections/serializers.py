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


class RegionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegionType
        fields = ["name"]
