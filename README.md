# grove

Grove RDF Ontology and Vocabulary Editor is a [Django]-based web
application for creating, editing, and publishing controlled vocabularies
in RDF.

## Development Environment Setup

* [VS Code Dev Container Setup](docs/DevelopmentEnvironmentVsCode.md)
* [Local Development Environment Setup](docs/DevelopmentEnvironmentLocal.md)

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
    git clone git@github.com:umd-lib/grove.git
    cd grove
    ```

2. Checkout the appropriate Git tag, branch, or commit for the Docker image.

3. Set up an "APP_TAG" environment variable:

    ```zsh
    export APP_TAG=<DOCKER_IMAGE_TAG>
    ```

   where \<DOCKER_IMAGE_TAG> is the Docker image tag to associate with the
   Docker image. This will typically be the Git tag for the application version,
   or some other identifier, such as a Git commit hash. For example, using the
   Git tag of "1.2.0":

    ```zsh
    export APP_TAG=1.2.0
    ```

    Alternatively, to use the Git branch and commit:

    ```zsh
    export GIT_BRANCH=`git rev-parse --abbrev-ref HEAD`
    export GIT_COMMIT_HASH=`git rev-parse HEAD`
    export APP_TAG=${GIT_BRANCH}-${GIT_COMMIT_HASH}
    ```

4. Switch to the Kubernetes "build" namespace:

    ```bash
    kubectl config use-context build
    ```

5. Create the "docker.lib.umd.edu/grove" Docker image:

    ```bash
    docker buildx build --no-cache --platform linux/amd64 --push --no-cache \
        --builder=kube  -f Dockerfile -t docker.lib.umd.edu/grove:$APP_TAG .
    ```

   The Docker image will be automatically pushed to the Nexus.

[Django]: https://www.djangoproject.com/
