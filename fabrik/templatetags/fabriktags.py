"""
jsprefix.py.
Registers A new tag for use in templates.

Define JS_PREFIX in the top-level settings.py file
and you can use {% load customtags %} and then {% js_prefix %} in
templates. Allows for relocation of content.
"""
from django.template import Library


register = Library()

def js_prefix():
    """
    Returns the string contained in the setting JS_PREFIX
    """
    try:
        from django.conf import settings
    except ImportError:
        return ''
    return settings.JS_PREFIX
    
js_prefix = register.simple_tag(js_prefix)
