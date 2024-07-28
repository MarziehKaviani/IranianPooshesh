from django.db import models
from django.utils import timezone


class Task(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    creation_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
