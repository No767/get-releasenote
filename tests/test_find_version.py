from contextlib import nullcontext
from typing import Optional, Union

import pytest
from conftest import VERSION_FILE_TMPL
from packaging.version import InvalidVersion

from main import Context, Parser


def test_find_version_file(ctx: Context, parser: Parser):
    assert (
        parser.find_version(ctx, version_file=(ctx.root / "file.py"), version=None)
        == "1.4.2"
    )


def test_supplied_version(ctx: Context, parser: Parser):
    assert parser.find_version(ctx, version_file=None, version="0.1.0") == "0.1.0"


@pytest.mark.parametrize(
    "version_file,supplied_version,exception",
    [
        ("hi.py", None, pytest.raises(ValueError, match="file")),
        ("fsoudbfsoufbedsoufbsoufbnsofd.py", "2026.01.5", nullcontext("2026.01.5")),
        (
            None,
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            pytest.raises(InvalidVersion),
        ),
        (
            "oh hi what's this",
            "i dont know it's a test case",
            pytest.raises(InvalidVersion),
        ),
        (None, None, pytest.raises(ValueError, match="Unable to")),
    ],
)
def test_invalid_versions(
    ctx: Context,
    parser: Parser,
    version_file: Optional[str],
    supplied_version: Optional[str],
    exception: Union[pytest.RaisesExc, nullcontext],
):
    with exception as e:
        assert e == parser.find_version(
            ctx, version_file=version_file, version=supplied_version
        )


def test_find___version___no_spaces(ctx: Context, parser: Parser) -> None:
    temp_version_file = (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="__version__='0.0.7'")
    )
    assert parser.find_version(ctx, version_file=temp_version_file, version=None) == "0.0.7"


def test_find___version___from_file_single_quotes(ctx: Context, parser: Parser) -> None:
    temp_version_file = (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="__version__ = '0.0.7'")
    )
    assert parser.find_version(ctx, version_file=temp_version_file, version=None) == "0.0.7"


def test_find___version___from_file_double_quotes(ctx: Context, parser: Parser) -> None:
    temp_version_file = (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line='__version__ = "0.0.7"')
    )
    assert parser.find_version(ctx, version_file=temp_version_file, version=None) == "0.0.7"


def test_find_version_from_file_single_quotes(ctx: Context, parser: Parser) -> None:
    temp_version_file = (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="version = '0.0.7'")
    )
    assert parser.find_version(ctx, version_file=temp_version_file, version=None) == "0.0.7"


def test_find_version_from_file_double_quotes(ctx: Context, parser: Parser) -> None:
    temp_version_file = (ctx.root / "file.py").write_text(
        VERSION_FILE_TMPL.format(version_line="version = '0.0.7'")
    )
    assert parser.find_version(ctx, version_file=temp_version_file, version=None) == "0.0.7"
