from django.db.models import Model, CharField, ForeignKey, CASCADE, TextChoices, PROTECT
from plastron.namespaces import namespace_manager, dc
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import NamespaceManager
from rdflib.util import from_n3


class Context(dict):
    def __init__(self, namespace_manager: NamespaceManager, **kwargs):
        self.namespace_manager = namespace_manager
        super().__init__(**kwargs)

    def add_prefix(self, uri: URIRef):
        for prefix, ns_uri in self.namespace_manager.namespaces():
            if uri.startswith(ns_uri):
                self[prefix] = str(ns_uri)
                return


class Vocabulary(Model):
    class Meta:
        verbose_name_plural = 'vocabularies'

    uri = CharField(max_length=256)

    def __str__(self) -> str:
        return self.uri

    @property
    def term_count(self) -> int:
        return self.terms.count()

    def graph(self) -> tuple[Graph, Context]:
        context = Context(
            namespace_manager,
            dc=str(dc),
        )
        graph = Graph()
        for term in self.terms.all():
            s = URIRef(term.uri)
            graph.add((s, dc.identifier, Literal(term.name)))
            for property in term.properties.all():
                p = URIRef(property.predicate.uri)
                context.add_prefix(p)
                if property.value_is_uri:
                    o = URIRef(property.value)
                    context.add_prefix(o)
                else:
                    o = Literal(property.value)
                graph.add((s, p, o))

        return graph, context


class Term(Model):
    vocabulary = ForeignKey(Vocabulary, on_delete=CASCADE, related_name='terms')
    name = CharField(max_length=256)

    @property
    def uri(self):
        return self.vocabulary.uri + self.name

    def __str__(self):
        return self.uri


class Predicate(Model):
    class ObjectType(TextChoices):
        URI_REF = 'URIRef'
        LITERAL = 'Literal'

    @classmethod
    def from_curie(cls, curie: str):
        return Predicate.objects.filter(uri=from_n3(curie)).first()

    uri = CharField(max_length=256)
    object_type = CharField(max_length=32, choices=ObjectType.choices)

    @property
    def curie(self) -> str:
        curie = URIRef(self.uri).n3(namespace_manager=namespace_manager)
        return curie if len(curie) < len(self.uri) else ''

    def __str__(self) -> str:
        return self.curie or self.uri

    @property
    def usage_count(self):
        return Property.objects.filter(predicate=self).count()


class Property(Model):
    class Meta:
        verbose_name_plural = 'properties'

    term = ForeignKey(Term, on_delete=CASCADE, related_name='properties')
    predicate = ForeignKey(Predicate, on_delete=PROTECT)
    value = CharField(max_length=1024)

    def __str__(self):
        return f'{self.term.uri} {self.predicate} {self.value}'

    @property
    def value_is_uri(self) -> bool:
        return self.predicate.object_type == Predicate.ObjectType.URI_REF

    @property
    def value_as_curie(self) -> str:
        curie = URIRef(self.value).n3(namespace_manager=namespace_manager)
        return curie if len(curie) <= len(self.value) else self.value

    @property
    def value_for_editing(self) -> str:
        return self.value_as_curie if self.value_is_uri else self.value
