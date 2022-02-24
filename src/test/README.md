# Tests

This is Bobs' test suite. Run all the tests with Pytest by simply running:

```bash
(.env) user:~/observatory$ pytest
```

Pytest configuration is in [`pyproject.toml`](../../pyproject.toml).

Test helpers and utilities are in [`conftest.py`](conftest.py).

* [Unit](#Unit)
* [Functional](#Functional)
* [Mypy](#Mypy)
* [Pylint](#Pylint)

## Unit

Includes all the unit tests, those are defined as tests which check and verify a specific and narrow part of the code.

E.g., a function, a method, a class, etc.

## Functional

Includes all functional tests, those are often, but not necessarily, complex tests which check and verify how the
software is intended to be used. I.e., functionalities and features.

E.g., test the interface to Bitcoin Core REST server, test an entire scan, etc.

Those often requires access to external resources, like Bitcoin Core. Currently, this is the list of related Pytest
markers (deselect desired tests with `-m 'not {marker}'`:

* `functional`: Any functional test has this mark.
* `require_rest`: Test that requires a configured Bitcoin Core REST server.

## Mypy

The `test_mypy.py` script runs `mypy` against the whole package (`/bobs`), deselect with `-m 'not mypy'`.

## Pylint

The `test_pylint.py` script runs `pylint` against the whole codebase (`/src`), deselect with `-m 'not pylint'`.
