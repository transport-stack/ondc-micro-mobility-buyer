import time

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from common.models import SingletonBaseModel
from ondc_micromobility_api.models import SystemParameters, MetroStation
from modules.models import get_model_cache_key


@receiver(post_save, sender=SystemParameters)
def update_parameters_cache(sender, instance, **kwargs):
    if isinstance(instance, SingletonBaseModel):
        cache_key = get_model_cache_key(instance)
        cache.set(cache_key, instance)


@receiver(post_delete, sender=SystemParameters)
def delete_parameters_cache(sender, instance, **kwargs):
    if isinstance(instance, SingletonBaseModel):
        cache_key = get_model_cache_key(instance)
        cache.delete(cache_key)


@receiver(post_save, sender=MetroStation)
@receiver(post_delete, sender=MetroStation)
def update_metro_stations_last_modified(sender, instance, **kwargs):
    system_parameters, created = SystemParameters.objects.get_or_create()
    system_parameters.metro_stations_last_modified = int(time.time())
    system_parameters.save()
