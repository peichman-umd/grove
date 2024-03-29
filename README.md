# grove

Grove RDF Ontology and Vocabulary Editor is a [Django]-based web 
application for creating, editing, and publishing controlled vocabularies 
in RDF.

## Development Environment

Requires:

* Python 3.11
* [Plastron] 4.0+ source code

### Setup

Clone Plastron and Grove from GitHub:

```bash
git clone git@github.com:umd-lib/plastron -b 4.0.0
git clone git@github.com:umd-lib/grove
cd grove
python -m venv --prompt "grove-py$(cat .python-version)" .venv
source .venv/bin/activate
pip install ../plastron/plastron-utils
pip install -e .
```

Create a `.env` file in the project base directory that looks like this:

```dotenv
DATABASE_URL=sqlite:///db.sqlite3
DEBUG=True
# SECRET_KEY can be anything with sufficient randomness
# one way of generating this is "uuidgen | shasum -a 256 | cut -c-64"
SECRET_KEY=...
```

Initialize the database:

```bash
./src/manage.py migrate
```

Run the application. The default port is 5000:

```bash
./src/manage.py runserver
```

The application will be running at <http://localhost:5000/>

To change the port, provide an argument to `runserver`, e.g.:

```bash
./src/manage.py runserver 5555
```

### Tests

To install test dependencies, install the `test` extra:

```bash
pip install -e .[test]
```

This project uses [pytest] in conjunction with the [pytest-django] plugin 
to run its tests. To run the test suite:

```bash
pytest
```

To run with coverage information:

```bash
pytest --cov src --cov-report term-missing
```

[Django]: https://www.djangoproject.com/
[Plastron]: https://github.com/umd-lib/plastron
[pytest]: https://pytest.org/
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/
