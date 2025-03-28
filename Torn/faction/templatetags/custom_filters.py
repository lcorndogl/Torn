from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0  # Return a default value if the input is not a dictionary

@register.filter
def div(value, divisor):
    return value / divisor

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def absolute(value):
    return abs(value)