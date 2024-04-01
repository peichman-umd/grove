import logging
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from os.path import basename
from pathlib import PurePath
from typing import IO, TextIO, TypeAlias, NamedTuple, cast
from xml.sax import SAXParseException

from django.core.validators import RegexValidator
from django.db.models import CASCADE, PROTECT, CharField, ForeignKey, Model, TextChoices
from plastron.namespaces import dc, namespace_manager as nsm, rdfs
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import NamespaceManager
from rdflib.parser import InputSource
from rdflib.plugin import PluginException
from rdflib.util import from_n3

from grove.settings import VOCAB_OUTPUT_DIR

logger = logging.getLogger(__name__)

vann = Namespace('http://purl.org/vocab/vann/')

VOCAB_FORMAT_LABELS = {
    'json-ld': 'JSON-LD',
    'turtle': 'Turtle',
    'rdfxml': 'RDF/XML',
    'ntriples': 'N-Triples',
}

GraphSource: TypeAlias = IO[bytes] | TextIO | InputSource | str | bytes | PurePath | None
"""Type alias for the types accepted by the `rdflib.Graph.parse()` method's `source` argument."""


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


class OutputFormat(NamedTuple):
    media_type: str
    extension: str
    label: str
    parameter_names: list[str]


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

    @property
    def basename(self) -> str:
        return basename(cast(str, self.uri).rstrip('#/'))

    def graph(self) -> tuple[Graph, Context]:
        context = Context(
            namespace_manager=nsm,
            dc=str(dc),
            rdfs=str(rdfs),
            vann=str(vann),
        )
        graph = Graph()
        vocab_subject = URIRef(cast(str, self.uri))
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

    OUTPUT_FORMATS = [
        OutputFormat('application/ld+json', 'jsonld', 'JSON-LD', ['json', 'jsonld', 'json-ld']),
        OutputFormat('text/turtle', 'ttl', 'Turtle', ['ttl', 'turtle']),
        OutputFormat('application/rdf+xml', 'xml', 'RDF/XML', ['rdf', 'xml', 'rdfxml', 'rdf/xml']),
        OutputFormat('application/n-triples', 'nt', 'N-Triples', ['nt', 'ntriples', 'n-triples']),
    ]

    def publish(self):
        graph, context = self.graph()
        for fmt in self.OUTPUT_FORMATS:
            file = VOCAB_OUTPUT_DIR / (self.basename + '.' + fmt.extension)
            with file.open(mode='wb') as fh:
                graph.serialize(destination=fh, format=fmt.media_type, context=context, encoding='utf-8')
            logger.info(f'Wrote {self} to {file} as {fmt.label}')

    def unpublish(self):
        for fmt in self.OUTPUT_FORMATS:
            file = VOCAB_OUTPUT_DIR / (self.basename + '.' + fmt.extension)
            file.unlink(missing_ok=True)

    @property
    def is_published(self) -> bool:
        return all(
            (VOCAB_OUTPUT_DIR / (self.basename + '.' + f.extension)).exists()
            for f in self.OUTPUT_FORMATS
        )

    @property
    def publication_date(self) -> datetime | None:
        if not self.is_published:
            return None
        return datetime.fromtimestamp(
            int((VOCAB_OUTPUT_DIR / (self.basename + '.' + self.OUTPUT_FORMATS[0].extension)).stat().st_mtime)
        )


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


class VocabularyImportError(Exception):
    pass


def import_vocabulary(file: GraphSource, uri: str, rdf_format: str) -> tuple[Vocabulary, bool, Counter]:
    count = Counter({
        'subjects': 0,
        'new_terms': 0,
        'new_properties': 0,
    })
    graph = Graph()
    try:
        graph.parse(file, format=rdf_format)
    except (ValueError, SAXParseException, PluginException, FileNotFoundError) as e:
        logger.error(
            f'Unable to import vocabulary: {e.__class__.__name__}: {e} '
            f'(file={file}, uri={uri}, rdf_format={rdf_format})'
        )
        raise VocabularyImportError from e
    vocab_subject = URIRef(uri)
    # check for existing predicates about the vocab (label, description, prefix)
    default_vocab_metadata = {
        'label': str(graph.value(
            subject=vocab_subject, predicate=rdfs.label, default=Literal(basename(uri.rstrip('#/')).title())
        )),
        'description': str(graph.value(
            subject=vocab_subject, predicate=dc.description, default=Literal('')
        )),
        'preferred_prefix': str(graph.value(
            subject=vocab_subject, predicate=vann.preferredNamespacePrefix, default=Literal('')
        )),
    }
    subjects = {s for s in set(graph.subjects()) if str(s).startswith(uri)}
    count['subjects'] = len(subjects)
    vocab, vocab_is_new = Vocabulary.objects.get_or_create(uri=uri, defaults=default_vocab_metadata)
    for subject in subjects:
        name = subject.replace(uri, '')
        term, term_is_new = Term.objects.get_or_create(vocabulary=vocab, name=name)
        if term_is_new:
            count['new_terms'] += 1
        for _, p, o in graph.triples((subject, None, None)):
            if isinstance(o, URIRef):
                object_type = Predicate.ObjectType.URI_REF
            else:
                object_type = Predicate.ObjectType.LITERAL
            if p == dc.identifier and str(o) == name:
                continue
            predicate, _ = Predicate.objects.get_or_create(uri=str(p), object_type=object_type)
            prop, prop_is_new = Property.objects.get_or_create(term=term, predicate=predicate, value=str(o))
            if prop_is_new:
                count['new_properties'] += 1

    return vocab, vocab_is_new, count
