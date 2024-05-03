# Development Environment - VS Code Dev Container

## Introduction

This document provides guidance on setting up a Grove development environment
using a VS Code Dev Container.

**Note:** See
[docs/DevelopmentEnvironmentLocal.md](DevelopmentEnvironmentLocal.md).
for setting up a development environment locally.

## Prerequisites

* On the local workstation, update the `/etc/hosts` file to add:

  ```zsh
  127.0.0.1 grove-local
  ```

## Application Setup

1) Clone Grove from GitHub:

    ```zsh
    git clone git@github.com:umd-lib/grove
    cd grove
    ```

2) Open the "grove" in VS Code directory. A notification to reopen the folder
   in a dev container will be displayed -- select "Reopen in Container"

   ℹ️ Note: If there isn't a notification, you can also open the command palette
   (CMD+Shift+P) and type `Dev Containers: Rebuild and Reopen in Container`

   The dev container will build the Docker image (if necessary), and install
   Python dependencies.

3) Download the `grove-test-lib-umd-edu-sp.crt` and
   `grove-test-lib-umd-edu-sp.key` files from the  "grove-local-saml" entry in
   LastPass into the "grove" directory.

   ℹ️ Note: When downloading the `grove-test-lib-umd-edu-sp.crt` file, Google
   Chrome will modify the file extension by default to ".cer". Be sure to to
   specify the ".crt" extension when downloading the file. Mozilla Firefox
   preserves the ".crt" extension.

4) In a VS Code terminal, run the following command to create a `.env` file
   in the project base directory, and populates it with default values:

    ```zsh
    cp env_example .env &&
       sed -i '/SAML_KEY_FILE=/cSAML_KEY_FILE=grove-test-lib-umd-edu-sp.key' .env &&
       sed -i '/SAML_CERT_FILE=/cSAML_CERT_FILE=grove-test-lib-umd-edu-sp.crt' .env &&
       sed -i '/SECRET_KEY=/c#SECRET_KEY=' .env
       sed -i '/XMLSEC1_PATH=/cXSMLSEC1_PATH=/usr/bin/xmlsec1' .env
    ```

    ℹ️ Note: The `SECRET_KEY` does not need to be set for local development, as
    a random string will be generated automatically, if necessary.

5) Initialize the database:

    ```zsh
    ./src/manage.py migrate
    ```

6) Load the default set of predicates:

    ```zsh
    ./src/manage.py load_predicates -f predicate.csv
    ```

7) Run the application. The default port is 15001; this is also the port that
   is registered with DIT to allow SAML authentication to work from local:

    ```zsh
    ./src/manage.py runserver
    ```

    The application will be running at <http://grove-local:15001/>

    ℹ️ Note: VS Code "launch" configurations are also available for running
    the above commands

    To change the port, provide an argument to `runserver`, e.g.:

    ```zsh
    ./src/manage.py runserver 5555
    ```

## Application Dependencies

The Python application dependencies (including test dependencies) are
automatically installed when the dev container is started.

To reinstall the dependencies, run

```zsh
pip install -e '.[test]'
```

## Tests

This project uses [pytest] in conjunction with the [pytest-django] plugin
to run its tests. To run the test suite:

```zsh
pytest
```

To run with coverage information:

```zsh
pytest --cov src --cov-report term-missing
```

[pytest]: https://pytest.org/
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/
