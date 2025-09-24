from rest_framework import serializers
from .models import Property, PropertyImage


class PropertyImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=False, required=False, allow_null=True)

    class Meta:
        model = PropertyImage
        fields = ["id", "property", "image", "created_at"]


class PropertySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=False, required=False, allow_null=True)
    images = PropertyImageSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ("owner", "created_at", "updated_at")
