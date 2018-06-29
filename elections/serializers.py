from rest_framework.serializers import ModelSerializer

from . import models


class RegionTypeSerializer(ModelSerializer):
    class Meta:
        model = models.RegionType
        fields = ["name"]
