from django import template
from django.urls import reverse
from django.conf import settings

register = template.Library()

@register.simple_tag
def project_menu_template():
    try:
        print ('tp m2k959', settings.PROJECT_MENU_TEMPLATE)
        return settings.PROJECT_MENU_TEMPLATE
    except:
        return None

@register.simple_tag
def global_css_file():
    try:
        return settings.GLOBAL_CSS_FILE
    except:
        return None


