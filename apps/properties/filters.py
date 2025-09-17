import django_filters
from .models import Property


class PropertyFilter(django_filters.FilterSet):
    """Filter class for Property model"""

    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    purchase_date_from = django_filters.DateFilter(field_name='purchase_date', lookup_expr='gte')
    purchase_date_to = django_filters.DateFilter(field_name='purchase_date', lookup_expr='lte')
    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Property
        fields = {
            'property_type': ['exact', 'in'],
            'contract_type': ['exact'],
            'is_active': ['exact'],
            'owner': ['exact'],
        }
