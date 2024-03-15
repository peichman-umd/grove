from contextlib import contextmanager

from django.core.validators import RegexValidator
from django.db.models import CASCADE, PROTECT, CharField, ForeignKey, Model, TextChoices
from plastron.namespaces import dc, namespace_manager as nsm, rdfs
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import NamespaceManager
from rdflib.util import from_n3

vann = Namespace('http://purl.org/vocab/vann/')

VOCAB_FORMAT_LABELS = {
    'json-ld': 'JSON-LD',
    'turtle': 'Turtle',
    'rdfxml': 'RDF/XML',
    'ntriples': 'N-Triples',
}


class VocabularyURIValidator(RegexValidator):
    regex = r'.+[/#]$'
    message = 'Must end with "/" or "#"'


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

    uri = CharField(max_length=256, validators=[VocabularyURIValidator()])
    label = CharField(max_length=256)
    description = CharField(max_length=1024, blank=True)
    preferred_prefix = CharField(max_length=32, blank=True)

    def __str__(self) -> str:
        return str(self.uri)

    @classmethod
    @contextmanager
    def with_uri(cls, uri: str):
        yield cls.objects.get(uri=uri)

    @property
    def term_count(self) -> int:
        return self.terms.count()

    def graph(self) -> tuple[Graph, Context]:
        context = Context(
            namespace_manager=nsm,
            dc=str(dc),
            rdfs=str(rdfs),
            vann=str(vann),
        )
        graph = Graph()
        vocab_subject = URIRef(self.uri)
        if self.label:
            graph.add((vocab_subject, rdfs.label, Literal(self.label)))
        if self.description:
            graph.add((vocab_subject, dc.description, Literal(self.description)))
        if self.preferred_prefix:
            graph.add((vocab_subject, vann.preferredNamespacePrefix, Literal(self.preferred_prefix)))
        for term in self.terms.all():
            s = URIRef(term.uri)
            graph.add((s, dc.identifier, Literal(term.name)))
            for prop in term.properties.all():
                p = URIRef(prop.predicate.uri)
                context.add_prefix(p)
                if prop.value_is_uri:
                    o = URIRef(prop.value)
                    context.add_prefix(o)
                else:
                    o = Literal(prop.value)
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
        curie = URIRef(str(self.uri)).n3(namespace_manager=nsm)
        return curie if len(curie) < len(str(self.uri)) else ''

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
        curie = URIRef(str(self.value)).n3(namespace_manager=nsm)
        return curie if len(curie) <= len(str(self.value)) else str(self.value)

    @property
    def value_for_editing(self) -> str:
        return self.value_as_curie if self.value_is_uri else self.value
