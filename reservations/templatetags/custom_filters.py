from django import template

register = template.Library()

@register.filter(name='exclude_keys')
def exclude_keys(dictionary, keys_to_exclude):
    keys = keys_to_exclude.split(',')
    return {k: v for k, v in dictionary.items() if k not in keys }

