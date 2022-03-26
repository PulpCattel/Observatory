"""
Run mypy automatically with Pytest, working directory should be the root
project folder (i.e., /observatory).
This module can also be called directly to provide a pre-configured wrapper around mypy.
"""
from shlex import split
from shutil import which
from subprocess import check_output, CalledProcessError

from pytest import mark

# For now we check only the Bobs package.
# Eventually we want to check the entire /src directory.
FILES = ('src/bobs',)
COMMAND = split(f"{which('mypy')} {' '.join(FILES)}")


def mypy_stdout() -> str:
    try:
        stdout = check_output(COMMAND, encoding='UTF-8')
    except CalledProcessError as err:
        stdout = err.output
    return stdout


@mark.mypy
def test_mypy() -> None:
    mypy_output = mypy_stdout()
    assert 'error' not in mypy_output
    assert 'warning' not in mypy_output
    assert 'Success: no issues found' in mypy_output


if __name__ == '__main__':
    print(mypy_stdout())
