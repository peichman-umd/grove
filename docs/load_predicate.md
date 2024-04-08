# Load Predicates

## Usage

The -f and --file arguments are the ones that really matter, the other options are just from inheriting Django's BaseCommand class.


```python
❯ src/manage.py load_predicates -h
usage: manage.py load_predicates [-h] -f FILE [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color] [--skip-checks]

A small management utility that reads a simple, 2-column CSV file (predicate, object_type), and does a get_or_create for each predicate listed.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  The 2-column CSV file (predicate, object_type)
  --version             Show program's version number and exit.
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions.
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
  --skip-checks         Skip system checks.
```

The CSV file is expected to be formatted as such:

| Predicate  | Object Type |
| ---------- | ----------- |
| rdfs:label |   Literal   |
| owl:sameAs |   URIRef    |

Where the Predicate is in its CURIE form and the Object Type being either URIRef or Literal
