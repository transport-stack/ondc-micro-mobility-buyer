from django.db import models

# Create your models here.
from django_countries.fields import CountryField


class City(models.Model):
    code = models.CharField(max_length=10, unique=True)
    display_name = models.CharField(max_length=200)
    country = CountryField(null=False, default="IN")

    def __str__(self):
        return f"{self.code}, {self.country}"

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ("display_name",)
        unique_together = ("code", "country")
