from rest_framework import serializers


class NullIntegerField(serializers.IntegerField):
    def to_representation(self, value):
        if not value:
            return None
        return super().to_representation(value)


class NullCharField(serializers.CharField):
    def to_representation(self, value):
        if not value:
            return None
        return super().to_representation(value)
