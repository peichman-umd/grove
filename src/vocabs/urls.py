from django.urls import path
from vocabs.views import GraphView, IndexView, PredicatesView, PropertyEditView, PropertyView, TermView, VocabularyView, NewPropertyView


urlpatterns = [
    path('', IndexView.as_view(), name='list_vocabularies'),
    path('<int:pk>', VocabularyView.as_view(), name='show_vocabulary'),
    path('<int:pk>/graph', GraphView.as_view(), name='show_graph'),
    path('terms/<int:pk>', TermView.as_view(), name='show_term'),
    path('properties/new', NewPropertyView.as_view(), name='new_property'),
    path('properties/<int:pk>', PropertyView.as_view(), name='show_property'),
    path('properties/<int:pk>/edit', PropertyEditView.as_view(), name='edit_property'),
    path('predicates', PredicatesView.as_view(), name='list_predicates'),
]
