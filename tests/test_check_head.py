import pytest

from main import Parser


def test_check_head_ok(parser: Parser) -> None:
    parser.check_head("1.2.3", "refs/tags/1.2.3")


def test_check_head_with_v_prefix(parser: Parser) -> None:
    parser.check_head("1.2.3", "refs/tags/v1.2.3")


def test_check_head_not_a_tag(parser: Parser) -> None:
    with pytest.raises(
        ValueError, match=r"Git head 'refs/heads/master' doesn't point at a tag"
    ):
        parser.check_head("1.2.3", "refs/heads/master")


def test_check_head_versions_mismatch(parser: Parser) -> None:
    with pytest.raises(
        ValueError, match=r"Git tag 'v2.3.4' mismatches with version '1.2.3"
    ):
        parser.check_head("1.2.3", "refs/tags/v2.3.4")
