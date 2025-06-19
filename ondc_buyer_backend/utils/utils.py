def get_cache_item(cache, key):
    return cache.get(key)


def set_cache_item(cache, key, value, timeout):
    cache.set(key, value, timeout=timeout)
