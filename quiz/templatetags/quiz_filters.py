from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary value by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)
