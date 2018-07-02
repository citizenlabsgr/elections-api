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


class DistrictCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DistrictCategory
        fields = ["name"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.District
        fields = ["kind", "name"]

    kind = serializers.CharField()
