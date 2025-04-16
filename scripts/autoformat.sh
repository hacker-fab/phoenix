#!/bin/bash

ruff check --fix python/*.py python/test/*.py
ruff format python/*.py python/test/*.py
