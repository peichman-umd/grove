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
git clone git@github.com:umd-lib/grove
cd grove
python -m venv --prompt "grove-py$(cat .python-version)" .venv
source .venv/bin/activate
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
[pytest]: https://pytest.org/
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/
