#!/usr/bin/env bash

echo "Setting up virtualenv"
virtualenv .
source bin/activate
echo "Python virtualenv setup successfully"

echo "Installing pip requirements..."
pip install -r requirements.txt

echo "Done"

