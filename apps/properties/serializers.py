from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True, required=False, allow_null=True)

    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ("owner", "created_at", "updated_at")
