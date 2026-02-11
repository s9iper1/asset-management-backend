"""
AI Advisor Chat Service using OpenAI GPT-5 Nano (Responses API).

Provides conversational AI assistance for property-related questions.
Optimized with prompt caching and minimal reasoning for lower cost.
"""

from openai import OpenAI
from django.conf import settings
from apps.properties.models import AIAdvisorChat
from apps.properties.services.credit_service import CreditService, InsufficientCreditsError


class AIAdvisorService:
    """Service for AI chatbot functionality"""

    # Pre-defined prompts for common questions
    PRE_DEFINED_PROMPTS = {
        'renovation_advice': {
            'en': "Suggest renovations that would increase the value of this property",
            'cs': "Navrhněte renovace, které by zvýšily hodnotu této nemovitosti"
        },
        'market_analysis': {
            'en': "Analyze current market conditions for this type of property in this area",
            'cs': "Analyzujte současné tržní podmínky pro tento typ nemovitosti v této oblasti"
        },
        'investment_potential': {
            'en': "Evaluate the investment potential of this property",
            'cs': "Vyhodnoťte investiční potenciál této nemovitosti"
        },
        'selling_tips': {
            'en': "Provide tips on how to best sell this property",
            'cs': "Poskytněte tipy, jak nejlépe prodat tuto nemovitost"
        },
        'rental_advice': {
            'en': "Advise on renting out this property effectively",
            'cs': "Poraďte, jak efektivně pronajmout tuto nemovitost"
        }
    }

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured in settings")

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def chat(self, user, property_obj, message='', prompt_type='freeform',
             predefined_prompt_id=None, language=None):
        """
        Send message to AI advisor and get response

        Args:
            user: User object
            property_obj: Property object
            message: User's message (or empty if using predefined)
            prompt_type: 'predefined' or 'freeform'
            predefined_prompt_id: ID of pre-defined prompt if applicable
            language: 'en' or 'cs' (defaults to user preference)

        Returns:
            tuple: (AIAdvisorChat object, new_balance)

        Raises:
            InsufficientCreditsError: If user lacks credits
        """
        language = language or user.preferred_language
        cost = CreditService.get_credit_cost('ai_advisor')

        # STEP 1: Deduct credits BEFORE calling API
        try:
            new_balance, txn_id = CreditService.deduct_credits(
                user=user,
                amount=cost,
                feature='ai_advisor',
                description=f"AI advisor chat for property {property_obj.id}",
                metadata={'property_id': property_obj.id, 'prompt_type': prompt_type}
            )
        except InsufficientCreditsError:
            raise

        # Build user message
        if prompt_type == 'predefined' and predefined_prompt_id:
            user_message = self.PRE_DEFINED_PROMPTS.get(
                predefined_prompt_id, {}
            ).get(language, message)
        else:
            user_message = message

        # STEP 2: Get AI response
        try:
            property_context = self._build_property_context(property_obj)
            system_prompt = self._get_system_prompt(language, property_context)

            # Recent history (last 5)
            previous_chats = AIAdvisorChat.objects.filter(
                property=property_obj
            ).order_by('-created_at')[:5]

            input_items = []

            # System + property context
            input_items.append({
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt
                    }
                ]
            })

            # Conversation history
            for chat in reversed(list(previous_chats)):
                input_items.append({
                    "role": "user",
                    "content": [{"type": "input_text", "text": chat.user_message}]
                })
                input_items.append({
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": chat.ai_response}]
                })

            # Current message
            input_items.append({
                "role": "user",
                "content": [{"type": "input_text", "text": user_message}]
            })

            # Call OpenAI
            response = self.client.responses.create(
                model=settings.OPENAI_MODEL,
                reasoning={"effort": "minimal"},
                max_output_tokens=500,
                text={"verbosity": "low"},
                input=input_items
            )

            ai_response = response.output_text
            tokens_used = response.usage.total_tokens

        except Exception as e:
            # STEP 3: Refund credits if API call failed
            CreditService.refund_credits(
                user=user,
                amount=cost,
                original_feature='ai_advisor',
                description=f"API call failed: {str(e)}"
            )
            raise Exception(f"OpenAI API error: {str(e)}")

        # STEP 4: Save chat
        chat = AIAdvisorChat.objects.create(
            property=property_obj,
            user=user,
            prompt_type=prompt_type,
            predefined_prompt_id=predefined_prompt_id or '',
            user_message=user_message,
            ai_response=ai_response,
            model_used=settings.OPENAI_MODEL,
            cost_credits=cost,
            tokens_used=tokens_used,
            language=language
        )

        return chat, new_balance

    def _build_property_context(self, property_obj):
        """Build context about the property for AI"""
        context = f"""
Property Information:
- Title: {property_obj.title}
- Type: {property_obj.get_property_type_display()}
- Address: {property_obj.address}
- Price: {property_obj.price} CZK
- Purchase Date: {property_obj.purchase_date or 'Not specified'}
- Contract Type: {property_obj.get_contract_type_display()}
"""
        if property_obj.story:
            context += f"- Story: {property_obj.story}\n"
        if property_obj.comment:
            context += f"- Notes: {property_obj.comment}\n"
        if property_obj.latitude and property_obj.longitude:
            context += f"- Location: {property_obj.latitude}, {property_obj.longitude}\n"

        return context

    def _get_system_prompt(self, language, property_context):
        """Get system prompt for AI advisor"""
        prompts = {
            'en': f"""You are a professional real estate advisor with expertise in property investment, renovation, and market analysis.

{property_context}

Provide helpful, accurate advice based on real estate best practices. Be concise but informative. When giving financial advice, remind users to consult qualified professionals for major decisions.""",

            'cs': f"""Jste profesionální poradce v oblasti nemovitostí s odborností v investicích do nemovitostí, renovacích a analýze trhu.

{property_context}

Poskytujte užitečné a přesné rady založené na osvědčených postupech v oblasti nemovitostí. Buďte struční, ale informativní. Při finančních doporučeních připomeňte uživatelům, aby se poradili s odborníky."""
        }

        return prompts.get(language, prompts['en'])

    def get_chat_history(self, property_obj, limit=20):
        """
        Get chat history for a property

        Args:
            property_obj: Property object
            limit: Number of messages to return

        Returns:
            QuerySet: Recent chats in chronological order
        """
        return AIAdvisorChat.objects.filter(
            property=property_obj
        ).order_by('created_at')[:limit]
