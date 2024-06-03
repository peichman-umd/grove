from vocabs.models import Vocabulary


def test_vocab_updated_trigger(post, vocab_uri):
    # create
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    # publish
    post(vocab_path + '/status', data={'publish': True})
    # update
    response = post(
        vocab_path,
        data={'uri': vocab_uri, 'label': 'bar', 'description': 'Vocab foo bar', 'preferred_prefix': 'foo'},
        headers={'HX-Request': 'true'},
    )
    assert 'HX-Trigger' in response.headers
    assert 'grove:vocabUpdated' in response.headers['HX-Trigger']


def test_term_added_trigger(post, vocab_uri):
    # create
    vocab_path = post('/vocabs/', data={'uri': vocab_uri}).wsgi_request.path
    # publish
    post(vocab_path + '/status', data={'publish': True})
    # add term
    vocab = Vocabulary.objects.get(uri=vocab_uri)
    response = post(
        vocab_path + '/forms/term',
        data={'name': 'Foo', 'vocabulary': vocab.id},
        headers={'HX-Request': 'true'},
    )
    assert 'HX-Trigger' in response.headers
    assert 'grove:termAdded' in response.headers['HX-Trigger']
    assert 'grove:vocabUpdated' in response.headers['HX-Trigger']
