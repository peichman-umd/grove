from django.http import HttpRequest
from django.urls import path

from vocabs.views import (GraphView, IndexView, NewPropertyView, PredicatesView, PrefixList, PropertyEditView,
                          PropertyView, TermView, VocabularyView, ImportFormView, VocabularyStatusView,
                          RootView, VocabularyPublicationFormView, NewTermFormView,
                          )

urlpatterns = [
    path('', RootView.as_view(), name='site_root'),
    path('vocabs/', IndexView.as_view(), name='list_vocabularies'),
    path('vocabs/<int:pk>', VocabularyView.as_view(), name='show_vocabulary'),
    path('vocabs/<int:pk>/graph', GraphView.as_view(), name='show_graph'),
    path('vocabs/<int:pk>/status', VocabularyStatusView.as_view(), name='vocabulary_status'),
    path('vocabs/<int:pk>/forms/publication', VocabularyPublicationFormView.as_view(), name='publication_form'),
    path('vocabs/<int:pk>/forms/term', NewTermFormView.as_view(), name='new_term_form'),
    path('terms/<int:pk>', TermView.as_view(), name='show_term'),
    path('properties/new', NewPropertyView.as_view(), name='new_property'),
    path('properties/<int:pk>', PropertyView.as_view(), name='show_property'),
    path('properties/<int:pk>/edit', PropertyEditView.as_view(), name='edit_property'),
    path('predicates', PredicatesView.as_view(), name='list_predicates'),
    path('prefixes', PrefixList.as_view(), name='list_prefixes'),
    path('import', ImportFormView.as_view(), name='import_form'),
]


def get_navigation_links(request: HttpRequest):
    if request.user.is_authenticated:
        return {
            'list_vocabularies': 'Vocabularies',
            'list_predicates': 'Predicates',
            'list_prefixes': 'Prefixes',
            'import_form': 'Import',
            '': f'Logged in as {request.user.username}',
            'saml2_logout': 'Log Out',
        }
    else:
        return {
            'saml2_login': 'Log In'
        }
