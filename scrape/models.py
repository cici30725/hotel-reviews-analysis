from django.db import models

# Create your models here.

class ScrapyModel(models.Model):
    unique_id = models.CharField(max_length=100, null=True)
    comments = models.TextField()
    hotel_name = models.CharField(max_length=100)

    @property
    def to_dict(self):
        data = {
            'hotel_name': self.hotel_name,
            'comments': self.comments
        }
        return data

    def __str__(self):
        return self.unique_id
