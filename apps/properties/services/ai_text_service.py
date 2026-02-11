"""
AI Text Generation Service using OpenAI GPT-5.

Generates property descriptions, stories, and marketing text for properties.
"""
import openai
from django.conf import settings
from decimal import Decimal
from apps.properties.models import AITextGeneration
from apps.properties.services.credit_service import CreditService, InsufficientCreditsError


class AIGenerationError(Exception):
    """Raised when AI text generation fails"""
    pass


class AITextService:
    """Service for GPT-5 text generation"""

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not configured in settings")

    def generate_property_text(
        self,
        user,
        property_obj,
        text_type='description',
        language=None,
        tone='professional'
    ):
        """
        Generate AI text for a property

        Args:
            user: User object
            property_obj: Property object
            text_type: 'description', 'story', or 'marketing'
            language: 'en' or 'cs' (defaults to user preference)
            tone: 'professional', 'casual', 'luxury'

        Returns:
            AITextGeneration object with generated text

        Raises:
            InsufficientCreditsError: If user lacks credits
            AIGenerationError: If generation fails
        """
        language = language or user.preferred_language
        cost = CreditService.get_credit_cost('ai_text')

        # STEP 1: Deduct credits BEFORE calling API
        try:
            new_balance, txn_id = CreditService.deduct_credits(
                user=user,
                amount=cost,
                feature='ai_text',
                description=f"AI {text_type} generation for property {property_obj.id}",
                metadata={'property_id': property_obj.id, 'text_type': text_type}
            )
        except InsufficientCreditsError as e:
            raise

        # STEP 2: Try to generate text
        try:
            prompt = self._build_prompt(property_obj, text_type, language, tone)
            system_prompt = self._get_system_prompt(text_type, language)

            response = openai.responses.create(
                model=settings.OPENAI_MODEL,
                reasoning={"effort": "minimal"},  # minimal, low, medium, high
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}],
                    },
                ],
                max_output_tokens=500,
                text={"verbosity": "low"}
            )

            generated_text = response.output_text
            tokens_used = response.usage.total_tokens

        except Exception as e:
            # STEP 3: Refund credits if API call failed
            CreditService.refund_credits(
                user=user,
                amount=cost,
                original_feature='ai_text',
                description=f"API call failed: {str(e)}"
            )
            raise AIGenerationError(f"OpenAI API error: {str(e)}")

        # STEP 4: Save generation
        generation = AITextGeneration.objects.create(
            property=property_obj,
            user=user,
            text_type=text_type,
            prompt=prompt,
            generated_text=generated_text,
            model_used=settings.OPENAI_MODEL,
            cost_credits=cost,
            tokens_used=tokens_used
        )

        return generation, new_balance

    def _build_prompt(self, property_obj, text_type, language, tone):
        """Build OpenAI prompt from property data"""
        property_info = f"""
Property Details:
- Title: {property_obj.title}
- Type: {property_obj.get_property_type_display()}
- Address: {property_obj.address}
- Price: {property_obj.price} CZK
- Purchase Date: {property_obj.purchase_date or 'Not specified'}
- Contract Type: {property_obj.get_contract_type_display()}
"""

        if property_obj.story:
            property_info += f"- Existing Story: {property_obj.story}\n"
        if property_obj.comment:
            property_info += f"- Comments: {property_obj.comment}\n"

        tasks = {
            'description': f"Write a {tone} property description",
            'story': f"Write an engaging property story",
            'marketing': f"Write compelling marketing text"
        }

        task = tasks.get(text_type, "Write about this property")

        return f"{task} in {language} for:\n{property_info}"

    def _get_system_prompt(self, text_type, language):
        """Get system prompt based on text type and language"""
        prompts = {
            'description': {
                'en': "You are a professional real estate copywriter. Write clear, accurate, and appealing property descriptions that highlight key features and benefits. Keep it concise and factual.",
                'cs': "Jste profesionální copywriter pro nemovitosti. Pište jasné, přesné a přitažlivé popisy nemovitostí, které zdůrazňují klíčové vlastnosti a výhody. Buďte struční a věcní."
            },
            'story': {
                'en': "You are a creative real estate storyteller. Write engaging narratives about properties that connect emotionally with potential buyers. Make it personal and memorable.",
                'cs': "Jste kreativní storyteller v oblasti nemovitostí. Pište poutavé příběhy o nemovitostech, které emocionálně propojují potenciální kupce. Buďte osobní a nezapomenutelní."
            },
            'marketing': {
                'en': "You are a marketing expert for real estate. Write persuasive copy that motivates action. Highlight unique selling points and create urgency.",
                'cs': "Jste marketingový expert v oblasti nemovitostí. Pište přesvědčivý text, který motivuje k akci. Zdůrazněte jedinečné prodejní výhody a vytvořte naléhavost."
            }
        }

        return prompts.get(text_type, {}).get(language, prompts['description']['en'])

    def apply_generated_text(self, generation_id, property_obj):
        """
        Apply AI-generated text to property

        Args:
            generation_id: ID of AITextGeneration
            property_obj: Property to update

        Returns:
            Updated property object
        """
        generation = AITextGeneration.objects.get(id=generation_id, property=property_obj)

        if generation.text_type == 'description':
            property_obj.ai_generated_description = generation.generated_text
        elif generation.text_type == 'story':
            property_obj.ai_generated_story = generation.generated_text

        property_obj.save()

        generation.was_applied = True
        generation.save(update_fields=['was_applied'])

        return property_obj
