from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Phase 1 ViewSets
router.register(r'agencies', views.AgencyViewSet, basename='agency')
router.register(r'communications', views.CommunicationViewSet, basename='communication')
router.register(r'credit-transactions', views.CreditTransactionViewSet, basename='credit-transaction')
router.register(r'ai-generations', views.AITextGenerationViewSet, basename='ai-generation')
router.register(r'ai-chats', views.AIAdvisorChatViewSet, basename='ai-chat')
router.register(r'emails', views.EmailLogViewSet, basename='email')

# Original ViewSets
router.register(r"property-images", views.PropertyImageViewSet, basename="property-image")
router.register(r"", views.PropertyViewSet, basename="property")

urlpatterns = [
    # Phase 1 Custom Endpoints
    path('auth/preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    path('auth/credit-balance/', views.CreditBalanceView.as_view(), name='credit-balance'),
    path('auth/column-preferences/', views.PropertyColumnPreferenceView.as_view(), name='column-preferences'),

    path('properties/<int:property_id>/generate-text/', views.PropertyAITextView.as_view(), name='property-generate-text'),
    path('properties/<int:property_id>/advisor-chat/', views.PropertyAIAdvisorView.as_view(), name='property-advisor-chat'),

    path('data-export/', views.DataExportView.as_view(), name='data-export'),
    path('data-import/', views.DataImportView.as_view(), name='data-import'),

    # Router URLs
    path('', include(router.urls)),
]
