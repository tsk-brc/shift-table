from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def to(value, arg):
    """Usage: {% for i in 1|to:12 %} ... {% endfor %} (1〜12)"""
    return range(int(value), int(arg) + 1)
