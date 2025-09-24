from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property, PropertyImage
from .serializers import PropertyImageSerializer, PropertySerializer
from .filters import PropertyFilter


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Staff/admin can see all properties
            return Property.objects.all()
        # Normal users only see their own
        return Property.objects.filter(owner=user)

    def perform_create(self, serializer):
        # assign logged-in user as the owner
        serializer.save(owner=self.request.user)


class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    http_method_names = ["get", "post", "delete"]