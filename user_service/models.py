from django.db import models

class UserProfile(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    medical_history = models.JSONField(default=dict)

    def __str__(self):   # pylint: disable=invalid-str-returned
        return self.name