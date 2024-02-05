from django.contrib import admin

from vocabs.models import Predicate, Property, Term, Vocabulary

admin.site.register(Predicate)
admin.site.register(Vocabulary)
admin.site.register(Term)
admin.site.register(Property)
