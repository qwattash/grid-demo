
# Path finding and other grid-based algorithms demo

## Setup

Install external requirements for the project:

1. qt5

Install python virtualenv and setup the virtual environment for the repo.

```sh
user@host $ virtualenv ./venv
user@host $ source ./venv/bin/activate
(venv) user@host $ pip install -r requirements.txt
```

Setup pylint git hooks, if pylint is installed in the virtualenv,
make sure you commit changes when the virtualenv is activated.

```sh
user@host $ ./hooks/repo_hooks_init.sh
```