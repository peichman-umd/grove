from django import template

register = template.Library()

NAVIGATION_LINKS = {
    'list_vocabularies': 'Vocabularies',
    'list_predicates': 'Predicates',
    'list_prefixes': 'Prefixes',
    'import_form': 'Import',
}


@register.inclusion_tag('vocabs/navigation.html', takes_context=True)
def navigation(context):
    context.update({'links': NAVIGATION_LINKS})
    return context
