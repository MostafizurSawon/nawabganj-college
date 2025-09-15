from django import template

register = template.Library()

@register.filter
def zip_lists(a, b):
    if a is None or b is None:
        return []
    return zip(a, b)
