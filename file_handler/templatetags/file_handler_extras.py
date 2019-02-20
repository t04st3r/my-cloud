from django import template

register = template.Library()


@register.inclusion_tag('breadcrumb.html')
def breadcrumb(folder):
    ancestors = folder.get_ancestors(include_self=True) if folder is not None else []
    return {'ancestors': ancestors}
