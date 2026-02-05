from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Property, PropertyImage, Agency, Communication, CreditTransaction,
    AITextGeneration, EmailLog, PropertyColumnPreference, AIAdvisorChat
)

User = get_user_model()


class PropertyImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=False, required=False, allow_null=True)

    class Meta:
        model = PropertyImage
        fields = ["id", "property", "image", "created_at"]


class PropertySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=False, required=False, allow_null=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Property
        fields = "__all__"
        read_only_fields = ("owner", "created_at", "updated_at")


# User & Preferences Serializers
class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'storage_mode', 'preferred_language', 'credit_balance']
        read_only_fields = ['id', 'email', 'credit_balance']


class CreditBalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_transactions = serializers.ListField(child=serializers.DictField(), max_length=5)


# Agency Serializers
class AgencySerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Agency
        fields = ['id', 'name', 'email', 'logo', 'phone', 'website', 'is_active',
                  'created_by', 'created_by_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


# Communication Serializers
class CommunicationSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)
    agency_name = serializers.CharField(source='agency.name', read_only=True)

    class Meta:
        model = Communication
        fields = ['id', 'property', 'property_title', 'agency', 'agency_name',
                  'subject', 'initial_message', 'message_thread', 'status',
                  'created_at', 'updated_at', 'last_message_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'last_message_at']


class AddMessageSerializer(serializers.Serializer):
    message = serializers.CharField()


# Credit Transaction Serializers
class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ['id', 'transaction_type', 'feature', 'amount', 'balance_before',
                  'balance_after', 'description', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


# AI Text Generation Serializers
class AITextGenerationRequestSerializer(serializers.Serializer):
    text_type = serializers.ChoiceField(choices=['description', 'story', 'marketing'])
    language = serializers.ChoiceField(choices=['en', 'cs'], required=False)
    tone = serializers.ChoiceField(choices=['professional', 'casual', 'luxury'], default='professional')


class AITextGenerationSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = AITextGeneration
        fields = ['id', 'property', 'property_title', 'text_type', 'generated_text',
                  'model_used', 'cost_credits', 'tokens_used', 'was_applied', 'created_at']
        read_only_fields = ['id', 'user', 'model_used', 'cost_credits', 'tokens_used',
                            'was_applied', 'created_at']


# Email Log Serializers
class EmailLogSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True, allow_null=True)

    class Meta:
        model = EmailLog
        fields = ['id', 'email_type', 'recipients', 'subject', 'body_preview',
                  'full_body', 'status', 'error_message', 'sent_at', 'created_at',
                  'property', 'property_title']
        read_only_fields = ['id', 'user', 'status', 'error_message', 'sent_at', 'created_at']


# Column Preferences Serializers
class PropertyColumnPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyColumnPreference
        fields = ['visible_columns', 'column_order', 'updated_at']
        read_only_fields = ['updated_at']


# AI Advisor Chat Serializers
class AIAdvisorChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)
    prompt_type = serializers.ChoiceField(choices=['predefined', 'freeform'], default='freeform')
    predefined_prompt_id = serializers.CharField(required=False, allow_blank=True)
    language = serializers.ChoiceField(choices=['en', 'cs'], required=False)


class AIAdvisorChatSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = AIAdvisorChat
        fields = ['id', 'property', 'property_title', 'prompt_type', 'predefined_prompt_id',
                  'user_message', 'ai_response', 'model_used', 'cost_credits',
                  'tokens_used', 'language', 'created_at']
        read_only_fields = ['id', 'user', 'model_used', 'cost_credits', 'tokens_used', 'created_at']
