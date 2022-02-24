"""
Run pylint automatically with Pytest, working directory should be the root
project folder (i.e., /observatory).
This module can also be called directly to provide a pre-configured wrapper around pylint.
"""

from io import StringIO
from shlex import split

from pylint.lint import Run
from pylint.reporters.text import TextReporter
from pytest import mark

# For now we check the entire /src directory.
FILES = ('src',)
DISABLED_CODES = [
    'C0301',
    'C0411',
    'C0116',
    'C0115',
    'C0103',
    'R0903',
    'C0413',
    'E0401',
    # no-name-in-module, disabled to avoid false positives, it's generally obvious to spot manually anyway
    'E0611',
]
ARGS = split(f'-f colorized -d {",".join(DISABLED_CODES)} --reports=yes -j 0')


def pylint_stdout() -> str:
    pylint_output = StringIO()
    reporter = TextReporter(pylint_output)
    Run(["src/", *ARGS], reporter=reporter, do_exit=False)
    # Retrieve and return the text report
    return pylint_output.getvalue()


@mark.pylint
def test_pylint() -> None:
    # TODO
    pass


if __name__ == '__main__':
    print(pylint_stdout())
