from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from . import models
from . import serializers


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_superuser and request.method == 'DELETE':
            return False
        return True


class BikeDamageViewSet(viewsets.ModelViewSet):
    queryset = models.BikeDamage.objects.all()
    serializer_class = serializers.BikeDamageSerializer


class BikeInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.BikeInventory.objects.all()
    serializer_class = serializers.BikeInventorySerializer


class BikeMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = models.BikeMaintenance.objects.all()
    serializer_class = serializers.BikeMaintenanceSerializer


class BikeGPSDamageViewSet(viewsets.ModelViewSet):
    queryset = models.BikeGPSDamage.objects.all()
    serializer_class = serializers.BikeGPSDamageSerializer


class BikeGPSInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.BikeGPSInventory.objects.all()
    serializer_class = serializers.BikeGPSInventorySerializer


class BikeGPSMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = models.BikeGPSMaintenance.objects.all()
    serializer_class = serializers.BikeGPSMaintenanceSerializer


class FleetAssetDamageViewSet(viewsets.ModelViewSet):
    queryset = models.FleetAssetDamage.objects.all()
    serializer_class = serializers.FleetAssetDamageSerializer


class FleetAssetInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.FleetAssetInventory.objects.all()
    serializer_class = serializers.FleetAssetInventorySerializer


class FleetAssetMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = models.FleetAssetMaintenance.objects.all()
    serializer_class = serializers.FleetAssetMaintenanceSerializer


class LockDamageViewSet(viewsets.ModelViewSet):
    queryset = models.LockDamage.objects.all()
    serializer_class = serializers.LockDamageSerializer


class LockInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.LockInventory.objects.all()
    serializer_class = serializers.LockInventorySerializer


class LockMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = models.LockMaintenance.objects.all()
    serializer_class = serializers.LockMaintenanceSerializer


class StopDamageViewSet(viewsets.ModelViewSet):
    queryset = models.StopDamage.objects.all()
    serializer_class = serializers.StopDamageSerializer


class StopInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.StopInventory.objects.all()
    serializer_class = serializers.StopInventorySerializer


class StopMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = models.StopMaintenance.objects.all()
    serializer_class = serializers.StopMaintenanceSerializer


class VehicleDamageViewSet(viewsets.ModelViewSet):
    queryset = models.VehicleDamage.objects.all()
    serializer_class = serializers.VehicleDamageSerializer


class VehicleInventoryViewSet(viewsets.ModelViewSet):
    queryset = models.VehicleInventory.objects.all()
    serializer_class = serializers.VehicleInventorySerializer


class VehicleMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = models.VehicleMaintenance.objects.all()
    serializer_class = serializers.VehicleMaintenanceSerializer


