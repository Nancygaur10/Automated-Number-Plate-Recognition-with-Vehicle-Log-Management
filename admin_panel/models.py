from django.db import models
from django.conf import settings

# Create your models here.
class PlateList(models.Model):

    TYPE_CHOICES = [
        ('BLACKLIST', 'Blacklist'),
        ('WHITELIST', 'Whitelist'),
    ]

    TAG_CHOICES = [
        ('Stolen', 'Stolen'),
        ('Unauthorized', 'Unauthorized'),
        ('Suspicious', 'Suspicious'),
    ]

    plate_number = models.CharField(max_length=20, unique=True)

    # Blacklist / Whitelist
    list_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    # 🔥 NEW: Type Tag
    tag = models.CharField(max_length=30, blank=True, null=True)

    # 🔥 NEW: Optional Image
    image = models.ImageField(upload_to='blacklist/', blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    added_on = models.DateTimeField(auto_now_add=True)

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.plate_number} ({self.list_type})"