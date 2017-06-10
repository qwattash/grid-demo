#!/bin/sh

base="$(git rev-parse --show-toplevel)"

echo "Attach git hooks in repo ${base}"

if [ -e "${base}/.git/hooks/pre-commit" ]; then
    echo "Pre commit hook already existing, skip. The hook must be merged manually."
    exit 0
fi

ln -s "${base}/hooks/pre-commit" "${base}/.git/hooks/pre-commit"

echo "Done."
