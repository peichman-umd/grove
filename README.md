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
git clone git@guthub.com:umd-lib/plastron -b 4.0.0
git clone git@github.com:umd-lib/grove
cd grove
python -m venv .venv
source .venv/bin/activate
pip install ../plastron/plastron-utils
pip install -e .
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

[Django]: https://www.djangoproject.com/
[Plastron]: http://github.com/umd-lib/plastron
