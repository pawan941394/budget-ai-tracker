from django.conf import settings
from django.conf import settings as django_settings
from django.db import models
from cryptography.fernet import Fernet
import base64
import hashlib


class Llmapikey(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="llm_api_key")
    provider = models.CharField(max_length=100, default="openai")
    api_key = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def _fernet():
        secret = django_settings.SECRET_KEY.encode("utf-8")
        digest = hashlib.sha256(secret).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def save(self, *args, **kwargs):
        if self.api_key and not self.api_key.startswith("gAAAAA"):
            self.api_key = self._fernet().encrypt(self.api_key.encode("utf-8")).decode("utf-8")
        super().save(*args, **kwargs)

    def get_api_key(self):
        return self._fernet().decrypt(self.api_key.encode("utf-8")).decode("utf-8")

    def __str__(self):
        return f"{self.user_id} - {self.provider}"
