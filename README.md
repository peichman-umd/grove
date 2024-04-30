# grove

Grove RDF Ontology and Vocabulary Editor is a [Django]-based web 
application for creating, editing, and publishing controlled vocabularies 
in RDF.

## Development Environment

Requires:

* Python 3.11

### Setup

Clone Grove from GitHub:

```bash
git clone git@github.com:umd-lib/grove
cd grove
python -m venv --prompt "grove-py$(cat .python-version)" .venv
source .venv/bin/activate
pip install -e .
```

Install `libxmlsec1`. This is required for the SAML authentication using
[djangosaml2].

On Mac, it is available via Homebrew:

```bash
brew install xmlsec1
```

On Debian or Ubuntu Linux, it is available via `apt`:

```bash
sudo apt-get install xmlsec1
```

Update the `/etc/hosts` file to add:

```
127.0.0.1 grove-local
```

Create a `.env` file in the project base directory that looks like this:

```dotenv
BASE_URL=http://grove-local:15001/
DATABASE_URL=sqlite:///db.sqlite3
DEBUG=True
ENVIRONMENT=development
# SECRET_KEY can be anything with sufficient randomness
# one way of generating this is "uuidgen | shasum -a 256 | cut -c-64"
SECRET_KEY=
# SAML_KEY_FILE and SAML_CERT_FILE may be absolute or relative paths; if they
# are relative they are relative to the project root directory
# These can be downloaded from the grove-local-saml note in the Shared-SSDR 
# folder on LastPass; note that local development uses the key and cert 
# from the test server, so the file basename is "grove-test-lib-umd-edu"
SAML_KEY_FILE=
SAML_CERT_FILE=
# absolute path to the xmlsec1 binary
# you can find this by running "which xmlsec1"
XMLSEC1_PATH=
# for local (i.e., non-HTTPS) development, we disable the secure cookie flag
SAML_SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=False
```

Initialize the database:

```bash
./src/manage.py migrate
```

Load the default set of predicates:

```bash
./src/manage.py load_predicates -f predicate.csv
```

Run the application. The default port is 15001; this is also the port that 
is registered with DIT to allow SAML authentication to work from local:

```bash
./src/manage.py runserver
```

The application will be running at <http://grove-local:15001/>

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

## Building the Docker Image for local testing

To build and run locally

```zsh
# Build
docker build -t docker.lib.umd.edu/grove:latest .

# Run
docker run -it \
-e DATABASE_URL=sqlite:///db.sqlite3 \
-e DEBUG=True \
-e SECRET_KEY=$(uuidgen | shasum -a 256 | cut -c-64) \
-e SERVER_PORT=5000 \
-p 5000:5000 \
docker.lib.umd.edu/grove:latest
```

## Building the Docker Image for K8s Deployment

The following procedure uses the Docker "buildx" functionality and the
Kubernetes "build" namespace to build the Docker image. This procedure should
work on both "arm64" and "amd64" MacBooks.

The image will be automatically pushed to the Nexus.

### Local Machine Setup

See <https://github.com/umd-lib/k8s/blob/main/docs/DockerBuilds.md> in
GitHub for information about setting up a MacBook to use the Kubernetes
"build" namespace.

### Creating the Docker image

1. In an empty directory, checkout the Git repository and switch into the
   directory:

    ```zsh
    $ git clone git@github.com:umd-lib/grove.git
    $ cd grove
    ```

2. Checkout the appropriate Git tag, branch, or commit for the Docker image.

3. Set up an "APP_TAG" environment variable:

    ```zsh
    $ export APP_TAG=<DOCKER_IMAGE_TAG>
    ```

   where \<DOCKER_IMAGE_TAG> is the Docker image tag to associate with the
   Docker image. This will typically be the Git tag for the application version,
   or some other identifier, such as a Git commit hash. For example, using the
   Git tag of "1.2.0":

    ```zsh
    $ export APP_TAG=1.2.0
    ```

    Alternatively, to use the Git branch and commit:

    ```zsh
    $ export GIT_BRANCH=`git rev-parse --abbrev-ref HEAD`
    $ export GIT_COMMIT_HASH=`git rev-parse HEAD`
    $ export APP_TAG=${GIT_BRANCH}-${GIT_COMMIT_HASH}
    ```

4. Switch to the Kubernetes "build" namespace:

    ```bash
    $ kubectl config use-context build
    ```

5. Create the "docker.lib.umd.edu/grove" Docker image:

    ```bash
    $ docker buildx build --no-cache --platform linux/amd64 --push --no-cache \
        --builder=kube  -f Dockerfile -t docker.lib.umd.edu/grove:$APP_TAG .
    ```

   The Docker image will be automatically pushed to the Nexus.

[Django]: https://www.djangoproject.com/
[Plastron]: https://github.com/umd-lib/plastron
[djangosaml2]: https://djangosaml2.readthedocs.io/
[pytest]: https://pytest.org/
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/
