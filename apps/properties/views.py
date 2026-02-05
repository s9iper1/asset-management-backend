from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal

from .models import (
    Property, PropertyImage, Agency, Communication, CreditTransaction,
    AITextGeneration, EmailLog, PropertyColumnPreference, AIAdvisorChat
)
from .serializers import (
    PropertyImageSerializer, PropertySerializer,
    AgencySerializer, CommunicationSerializer, AddMessageSerializer,
    CreditTransactionSerializer, AITextGenerationRequestSerializer,
    AITextGenerationSerializer, EmailLogSerializer,
    PropertyColumnPreferenceSerializer, AIAdvisorChatRequestSerializer,
    AIAdvisorChatSerializer, UserPreferencesSerializer, CreditBalanceSerializer
)
from .filters import PropertyFilter

from apps.properties.services.credit_service import CreditService, InsufficientCreditsError
from apps.properties.services.ai_text_service import AITextService, AIGenerationError
from apps.properties.services.ai_advisor_service import AIAdvisorService
from apps.properties.services.email_service import EmailService
from apps.properties.services.encryption_service import EncryptionService


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


# ============================================================================
# User & Authentication Views
# ============================================================================

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """Get and update user preferences"""
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CreditBalanceView(generics.GenericAPIView):
    """Get user credit balance and recent transactions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        recent = CreditTransaction.objects.filter(user=user).order_by('-created_at')[:5]

        recent_data = []
        for txn in recent:
            recent_data.append({
                'id': txn.id,
                'type': txn.transaction_type,
                'feature': txn.feature,
                'amount': str(txn.amount),
                'created_at': txn.created_at.isoformat()
            })

        serializer = CreditBalanceSerializer({
            'balance': user.credit_balance,
            'recent_transactions': recent_data
        })
        return Response(serializer.data)


class CreditTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """View credit transaction history"""
    serializer_class = CreditTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CreditTransaction.objects.filter(user=self.request.user)


# ============================================================================
# Agency Management
# ============================================================================

class AgencyViewSet(viewsets.ModelViewSet):
    """CRUD operations for agencies"""
    serializer_class = AgencySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users see their own agencies, staff see all
        if self.request.user.is_staff:
            return Agency.objects.all()
        return Agency.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ============================================================================
# Communication Management
# ============================================================================

class CommunicationViewSet(viewsets.ModelViewSet):
    """Manage communications with agencies"""
    serializer_class = CommunicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Communication.objects.filter(user=self.request.user)

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by property
        property_id = self.request.query_params.get('property_id')
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        return queryset.select_related('property', 'agency')

    def perform_create(self, serializer):
        communication = serializer.save(user=self.request.user)

        # Automatically send email if status is 'sent'
        if communication.status == 'sent':
            EmailService.send_agency_inquiry(communication)

    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        """Add a message to the communication thread"""
        communication = self.get_object()
        serializer = AddMessageSerializer(data=request.data)

        if serializer.is_valid():
            message = serializer.validated_data['message']

            # Add message to thread
            thread = communication.message_thread or []
            thread.append({
                'sender': 'user',
                'message': message,
                'timestamp': timezone.now().isoformat()
            })

            communication.message_thread = thread
            communication.last_message_at = timezone.now()
            communication.save(update_fields=['message_thread', 'last_message_at'])

            return Response(CommunicationSerializer(communication).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# AI Text Generation
# ============================================================================

class AITextGenerationViewSet(viewsets.ReadOnlyModelViewSet):
    """View AI text generation history"""
    serializer_class = AITextGenerationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AITextGeneration.objects.filter(user=self.request.user)

        # Filter by property
        property_id = self.request.query_params.get('property_id')
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        return queryset.select_related('property')

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply generated text to property"""
        generation = self.get_object()

        if not generation.property:
            return Response(
                {'error': 'No property associated with this generation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = AITextService()
        property_obj = service.apply_generated_text(generation.id, generation.property)

        return Response({
            'message': 'AI-generated text applied to property',
            'property_id': property_obj.id,
            'field_updated': f'ai_generated_{generation.text_type}'
        })


class PropertyAITextView(generics.GenericAPIView):
    """Generate AI text for a property"""
    permission_classes = [IsAuthenticated]

    def post(self, request, property_id):
        # TODO: Add owner check
        # property_obj = Property.objects.get(id=property_id, owner=request.user)
        property_obj = Property.objects.get(id=property_id)
        serializer = AITextGenerationRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = AITextService()
            generation, new_balance = service.generate_property_text(
                user=request.user,
                property_obj=property_obj,
                text_type=serializer.validated_data['text_type'],
                language=serializer.validated_data.get('language'),
                tone=serializer.validated_data.get('tone', 'professional')
            )

            return Response({
                'generation_id': generation.id,
                'text_type': generation.text_type,
                'generated_text': generation.generated_text,
                'cost_credits': str(generation.cost_credits),
                'new_balance': str(new_balance),
                'tokens_used': generation.tokens_used
            })

        except InsufficientCreditsError as e:
            return Response(
                {
                    'error': 'insufficient_credits',
                    'message': str(e),
                    'current_balance': str(request.user.credit_balance)
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        except AIGenerationError as e:
            return Response(
                {'error': 'generation_failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# AI Advisor Chat
# ============================================================================

class AIAdvisorChatViewSet(viewsets.ReadOnlyModelViewSet):
    """View AI advisor chat history"""
    serializer_class = AIAdvisorChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AIAdvisorChat.objects.filter(user=self.request.user)

        # Filter by property
        property_id = self.request.query_params.get('property_id')
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        return queryset.select_related('property')


class PropertyAIAdvisorView(generics.GenericAPIView):
    """Chat with AI advisor about a property"""
    permission_classes = [IsAuthenticated]

    def post(self, request, property_id):
        property_obj = Property.objects.get(id=property_id, owner=request.user)
        serializer = AIAdvisorChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = AIAdvisorService()
            chat, new_balance = service.chat(
                user=request.user,
                property_obj=property_obj,
                message=serializer.validated_data.get('message', ''),
                prompt_type=serializer.validated_data.get('prompt_type', 'freeform'),
                predefined_prompt_id=serializer.validated_data.get('predefined_prompt_id'),
                language=serializer.validated_data.get('language')
            )

            return Response({
                'chat_id': chat.id,
                'user_message': chat.user_message,
                'ai_response': chat.ai_response,
                'cost_credits': str(chat.cost_credits),
                'new_balance': str(new_balance),
                'language': chat.language
            })

        except InsufficientCreditsError as e:
            return Response(
                {
                    'error': 'insufficient_credits',
                    'message': str(e),
                    'current_balance': str(request.user.credit_balance)
                },
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        except Exception as e:
            return Response(
                {'error': 'chat_failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, property_id):
        """Get chat history for property"""
        property_obj = Property.objects.get(id=property_id, owner=request.user)
        chats = AIAdvisorChat.objects.filter(property=property_obj).order_by('created_at')
        serializer = AIAdvisorChatSerializer(chats, many=True)
        return Response({'count': chats.count(), 'results': serializer.data})


# ============================================================================
# Email History
# ============================================================================

class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View email history"""
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EmailLog.objects.filter(user=self.request.user)

        # Filter by property
        property_id = self.request.query_params.get('property_id')
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        # Filter by email type
        email_type = self.request.query_params.get('email_type')
        if email_type:
            queryset = queryset.filter(email_type=email_type)

        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.select_related('property', 'communication')


# ============================================================================
# Column Preferences
# ============================================================================

class PropertyColumnPreferenceView(generics.RetrieveUpdateAPIView):
    """Get and update property column preferences"""
    serializer_class = PropertyColumnPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, created = PropertyColumnPreference.objects.get_or_create(user=self.request.user)
        return obj


# ============================================================================
# File Mode Export/Import
# ============================================================================

class DataExportView(generics.GenericAPIView):
    """Export all user data encrypted"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password required for encryption'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Collect all user data
        data = {
            'user': {
                'email': user.email,
                'name': user.name,
                'preferred_language': user.preferred_language,
                'credit_balance': str(user.credit_balance)
            },
            'properties': list(Property.objects.filter(owner=user).values()),
            'agencies': list(Agency.objects.filter(created_by=user).values()),
            'communications': list(Communication.objects.filter(user=user).values()),
            'credit_transactions': list(CreditTransaction.objects.filter(user=user).values()),
            'ai_generations': list(AITextGeneration.objects.filter(user=user).values()),
            'ai_chats': list(AIAdvisorChat.objects.filter(user=user).values()),
            'export_date': timezone.now().isoformat()
        }

        # Encrypt data
        encrypted = EncryptionService.encrypt_data(data, password)

        # Return as downloadable file
        response = HttpResponse(encrypted, content_type='application/octet-stream')
        filename = f'real_estate_data_{timezone.now().strftime("%Y%m%d_%H%M%S")}.enc'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class DataImportView(generics.GenericAPIView):
    """Import encrypted user data"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password required for decryption'},
                status=status.HTTP_400_BAD_REQUEST
            )

        encrypted_file = request.FILES['file']
        encrypted_bytes = encrypted_file.read()

        try:
            # Decrypt data
            data = EncryptionService.decrypt_data(encrypted_bytes, password)

            # Import data (simplified - in production, add merge_strategy logic)
            properties_count = len(data.get('properties', []))
            agencies_count = len(data.get('agencies', []))

            # TODO: Implement actual import logic with merge strategy

            return Response({
                'message': 'Data imported successfully',
                'properties_imported': properties_count,
                'agencies_imported': agencies_count,
                'communications_imported': len(data.get('communications', []))
            })

        except ValueError as e:
            return Response(
                {'error': 'Decryption failed', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )