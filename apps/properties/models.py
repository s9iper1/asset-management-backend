from django.db import models
from django.conf import settings


class Property(models.Model):
    class PropertyType(models.TextChoices):
        HOUSE = "house", "House"
        APARTMENT = "apartment", "Apartment"
        LAND = "land", "Land"
        COMMERCIAL = "commercial", "Commercial"
        OTHER = "other", "Other"

    class ContractType(models.TextChoices):
        NONE = "none", "No Contract"
        RENT = "rent", "Rent"
        LEASE = "lease", "Lease"
        MORTGAGE = "mortgage", "Mortgage"
        OTHER = "other", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties"
    )
    title = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.OTHER
    )
    purchase_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contract_type = models.CharField(
        max_length=20, choices=ContractType.choices, default=ContractType.NONE
    )
    available_from = models.DateField(null=True, blank=True)
    conditions = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    comment = models.TextField(blank=True)
    story = models.TextField(blank=True)

    # Featured image
    image = models.ImageField(
        upload_to="property_images/featured/", null=True, blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Phase 1 additions - API integration fields
    parcel_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cadastral parcel number"
    )
    cadastral_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Full response from cadastral API"
    )
    valuo_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Valuation data from Valuo.cz API"
    )
    realman_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Realman API response data"
    )
    ai_generated_description = models.TextField(
        blank=True,
        help_text="AI-generated property description"
    )
    ai_generated_story = models.TextField(
        blank=True,
        help_text="AI-generated property story"
    )

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.property_type})"


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="property_images/gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Image for {self.property.title}"


# =============================================================================
# Phase 1 New Models
# =============================================================================

class Agency(models.Model):
    """Real estate agencies that users can communicate with"""

    name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField()
    logo = models.ImageField(upload_to='agency_logos/', null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    # Multi-tenant support
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_agencies'
    )
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Agencies"
        ordering = ['name']

    def __str__(self):
        return self.name


class Communication(models.Model):
    """Communication threads between users and agencies regarding properties"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('replied', 'Agency Replied'),
        ('closed', 'Closed'),
    ]

    # Relations
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='communications'
    )
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='communications'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communications'
    )

    # Content
    subject = models.CharField(max_length=255)
    initial_message = models.TextField()
    message_thread = models.JSONField(
        default=list,
        help_text="Array of message objects: [{sender, message, timestamp}]"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['agency', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.agency.name}: {self.subject}"


class CreditTransaction(models.Model):
    """Log of all credit purchases and deductions"""

    TRANSACTION_TYPES = [
        ('purchase', 'Credit Purchase'),
        ('deduction', 'Feature Usage'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus Credits'),
    ]

    FEATURE_TYPES = [
        ('ai_text', 'AI Text Generation'),
        ('ai_advisor', 'AI Advisor Chat'),
        ('valuo_api', 'Valuo.cz API'),
        ('realman_api', 'Realman API'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credit_transactions'
    )

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    feature = models.CharField(
        max_length=50,
        choices=FEATURE_TYPES,
        blank=True,
        help_text="Feature that consumed credits (for deductions)"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Positive for purchases/bonuses, negative for deductions"
    )
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text="Additional context (e.g., property_id, payment_id)"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.amount} credits ({self.transaction_type})"


class AITextGeneration(models.Model):
    """History of AI-generated text for properties"""

    TEXT_TYPES = [
        ('description', 'Property Description'),
        ('story', 'Property Story'),
        ('marketing', 'Marketing Text'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='ai_generations',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_generations'
    )

    # Input
    text_type = models.CharField(max_length=20, choices=TEXT_TYPES)
    prompt = models.TextField(help_text="User's input or property details")

    # Output
    generated_text = models.TextField()
    model_used = models.CharField(max_length=50, default='gpt-4o')

    # Cost
    cost_credits = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Credits deducted for this generation"
    )
    tokens_used = models.IntegerField(default=0)

    # Metadata
    was_applied = models.BooleanField(
        default=False,
        help_text="Whether user applied this text to the property"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"AI {self.text_type} for {self.property or 'N/A'}"


class EmailLog(models.Model):
    """Log of all sent emails for audit and filtering"""

    EMAIL_TYPES = [
        ('inquiry', 'Agency Inquiry'),
        ('sale', 'Sale Inquiry'),
        ('notification', 'Anniversary Notification'),
        ('system', 'System Email'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_emails'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_emails'
    )
    communication = models.ForeignKey(
        Communication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Email details
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)
    recipients = models.JSONField(help_text="List of recipient emails")
    subject = models.CharField(max_length=255)
    body_preview = models.TextField(
        max_length=500,
        help_text="First 500 chars of email body"
    )
    full_body = models.TextField()

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)

    # Celery metadata
    celery_task_id = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'email_type', '-created_at']),
            models.Index(fields=['property', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.email_type}: {self.subject} to {len(self.recipients) if isinstance(self.recipients, list) else 0} recipient(s)"


class PropertyColumnPreference(models.Model):
    """User's custom column visibility and ordering preferences"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='column_preferences'
    )

    # Available columns (for reference)
    AVAILABLE_COLUMNS = [
        'title', 'address', 'property_type', 'price', 'purchase_date',
        'contract_type', 'available_from', 'is_active', 'created_at',
        'updated_at', 'parcel_number', 'contact'
    ]

    # User's selected columns (JSON array)
    visible_columns = models.JSONField(
        default=list,
        help_text="List of visible column identifiers",
        blank=True
    )

    # Column ordering (JSON array)
    column_order = models.JSONField(
        default=list,
        help_text="Ordered list of column identifiers",
        blank=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Property Column Preference"

    def __str__(self):
        return f"Column prefs for {self.user.email}"

    def get_visible_columns(self):
        """Return visible columns or default if empty"""
        if self.visible_columns:
            return self.visible_columns
        # Default columns
        return ['title', 'address', 'property_type', 'price', 'created_at']


class AIAdvisorChat(models.Model):
    """AI chatbot conversation history per property"""

    PROMPT_TYPES = [
        ('predefined', 'Pre-defined Prompt'),
        ('freeform', 'Free-form Question'),
    ]

    # Relations
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='advisor_chats'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advisor_chats'
    )

    # Message details
    prompt_type = models.CharField(max_length=20, choices=PROMPT_TYPES)
    predefined_prompt_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of pre-defined prompt if used (e.g., 'renovation_advice')"
    )
    user_message = models.TextField(help_text="User's question or message")

    # AI response
    ai_response = models.TextField(help_text="AI's response")
    model_used = models.CharField(max_length=50, default='gpt-4o')

    # Cost tracking
    cost_credits = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Credits charged for this chat"
    )
    tokens_used = models.IntegerField(default=0)

    # Metadata
    language = models.CharField(
        max_length=10,
        help_text="Language of the conversation"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']  # Chronological order for chat history
        indexes = [
            models.Index(fields=['property', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Chat for {self.property.title}: {self.user_message[:50]}..."

