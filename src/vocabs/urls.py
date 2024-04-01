from django.urls import path

from vocabs.views import (GraphView, IndexView, NewPropertyView, PredicatesView, PrefixList, PropertyEditView,
                          PropertyView, TermView, VocabularyView, TermsView, ImportFormView, PublishedVocabularyView)

urlpatterns = [
    path('', IndexView.as_view(), name='list_vocabularies'),
    path('<int:pk>', VocabularyView.as_view(), name='show_vocabulary'),
    path('<int:pk>/terms', TermsView.as_view(), name='list_terms'),
    path('<int:pk>/graph', GraphView.as_view(), name='show_graph'),
    path('<int:pk>/published', PublishedVocabularyView.as_view(), name='publish_vocabulary'),
    path('terms/<int:pk>', TermView.as_view(), name='show_term'),
    path('properties/new', NewPropertyView.as_view(), name='new_property'),
    path('properties/<int:pk>', PropertyView.as_view(), name='show_property'),
    path('properties/<int:pk>/edit', PropertyEditView.as_view(), name='edit_property'),
    path('predicates', PredicatesView.as_view(), name='list_predicates'),
    path('prefixes', PrefixList.as_view(), name='list_prefixes'),
    path('import', ImportFormView.as_view(), name='import_form'),
]
