from rest_framework import viewsets, permissions
from .models import Property
from .serializers import PropertySerializer


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # only show properties of the logged-in user
        return Property.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # assign logged-in user as the owner
        serializer.save(owner=self.request.user)
