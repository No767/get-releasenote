import pathlib
from typing import Optional

import pytest

from main import Context, Parser

VERSION_FILE_TMPL = """\
from ._inner import Foo, Bar, spam_ham

{version_line}

__all__ = ("Foo", "Bar", "spam_ham")
"""


@pytest.fixture
def ctx(tmp_path: pathlib.Path, version: Optional[str] = None) -> Context:
    temp_version_file = tmp_path / "file.py"
    temp_version_file.write_text(
        VERSION_FILE_TMPL.format(version_line="__version__ = '1.4.2'")
    )
    return Context(tmp_path, version)


@pytest.fixture
def parser() -> Parser:
    return Parser(changes_file="changelog.md", name="get-releasenote")
