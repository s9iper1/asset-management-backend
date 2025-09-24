from rest_framework.routers import DefaultRouter
from .views import PropertyImageViewSet, PropertyViewSet

router = DefaultRouter()
router.register(r"property-images", PropertyImageViewSet, basename="property-image")
router.register(r"", PropertyViewSet, basename="property")

urlpatterns = router.urls
