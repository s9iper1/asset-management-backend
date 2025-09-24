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
