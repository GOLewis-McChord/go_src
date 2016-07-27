from rest_framework import serializers

from . import models


class MetadataSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'sheet',
            'date',
            'route',
            'driver',
            'vehicle',
            'login',
            'start_mileage',
            'end_mileage',
            'logout'
        )
        model = models.Metadata


class EntrySerializer(serializers.ModelSerializer):
    class Entry:
        fields = (
            'metadata',
            'on',
            'time',
            'count',
            'off'
        )
        model = models.Entry
