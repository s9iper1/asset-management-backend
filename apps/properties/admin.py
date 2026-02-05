from django.contrib import admin
from .models import (
    Property, PropertyImage, Agency, Communication, CreditTransaction,
    AITextGeneration, EmailLog, PropertyColumnPreference, AIAdvisorChat
)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'property_type', 'price', 'is_active', 'created_at')
    list_filter = ('property_type', 'contract_type', 'is_active', 'created_at')
    search_fields = ('title', 'address', 'parcel_number')
    list_select_related = ('owner',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'created_at')
    list_filter = ('created_at',)
    list_select_related = ('property',)


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email')
    list_select_related = ('created_by',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('property', 'agency', 'user', 'status', 'created_at', 'last_message_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'initial_message')
    list_select_related = ('property', 'agency', 'user')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'feature', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'feature', 'created_at')
    search_fields = ('user__email', 'description')
    list_select_related = ('user',)
    readonly_fields = ('created_at',)


@admin.register(AITextGeneration)
class AITextGenerationAdmin(admin.ModelAdmin):
    list_display = ('property', 'user', 'text_type', 'model_used', 'cost_credits', 'was_applied', 'created_at')
    list_filter = ('text_type', 'was_applied', 'created_at')
    search_fields = ('generated_text',)
    list_select_related = ('property', 'user')
    readonly_fields = ('created_at',)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'email_type', 'status', 'sent_at', 'created_at')
    list_filter = ('email_type', 'status', 'created_at')
    search_fields = ('subject', 'recipients')
    list_select_related = ('user', 'property', 'communication')
    readonly_fields = ('created_at',)


@admin.register(PropertyColumnPreference)
class PropertyColumnPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    search_fields = ('user__email',)
    list_select_related = ('user',)


@admin.register(AIAdvisorChat)
class AIAdvisorChatAdmin(admin.ModelAdmin):
    list_display = ('property', 'user', 'prompt_type', 'language', 'cost_credits', 'created_at')
    list_filter = ('prompt_type', 'language', 'created_at')
    search_fields = ('user_message', 'ai_response')
    list_select_related = ('property', 'user')
    readonly_fields = ('created_at',)