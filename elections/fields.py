from rest_framework import serializers


class NullIntegerField(serializers.IntegerField):
    def to_representation(self, value):
        if value == 0:
            return None
        return super().to_representation(value)
