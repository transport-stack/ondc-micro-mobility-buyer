from django.db import models


class SingletonBaseModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# Create your models here.
class SystemParameters(SingletonBaseModel):
    class Meta:
        verbose_name = "System Parameter"
        verbose_name_plural = "System Parameters"

    def __str__(self):
        return "System Parameters"
