from textwrap import dedent

import pytest

from main import Context, Parser

START_LINE = "<!-- towncrier release notes start -->"
HEAD_LINE = r"##\s{name}\s\[{version}\]\(.*\)[\s-]*({date})"


def test_parse_no_start_line(ctx: Context, parser: Parser) -> None:
    with pytest.raises(ValueError, match=r"Cannot find TOWNCRIER start mark"):
        parser._parse(
            ctx,
            changes="hi",
            start_line=START_LINE,
            head_line=HEAD_LINE,
            fix_issue_regex=None,
            fix_issue_repl=None,
        )


def test_parse_no_head_line(ctx: Context, parser: Parser) -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}
      NO-VERSION
    """
    )
    with pytest.raises(ValueError, match=r"Cannot find TOWNCRIER version head mark"):
        parser._parse(
            ctx,
            changes=CHANGES,
            start_line=START_LINE,
            head_line=HEAD_LINE,
            fix_issue_regex=None,
            fix_issue_repl=None,
        )


def test_parse_version_older(ctx: Context, parser: Parser) -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}

    
      ## get-releasenote [1.2.4](https://github.com/No767/get-release/tree/1.2.4) - 2025-12-24

    """
    )
    with pytest.raises(
        ValueError, match=r"The distribution version 1.2.3 is older than 1.2.4"
    ):
        ctx.version = parser.find_version(ctx, version_file=None, version="1.2.3")
        parser._parse(
            ctx,
            changes=CHANGES,
            start_line=START_LINE,
            head_line=HEAD_LINE,
            fix_issue_regex=None,
            fix_issue_repl=None,
        )


def test_parse_version_younger(ctx: Context, parser: Parser) -> None:
    CHANGES = dedent(
        f"""\
      {START_LINE}

    
      ## get-releasenote [1.2.4](https://github.com/No767/get-release/tree/1.2.4) - 2025-12-24

    """
    )
    with pytest.raises(
        ValueError, match=r"The distribution version 1.2.5 is younger than 1.2.4"
    ):
        ctx.version = parser.find_version(ctx, version_file=None, version="1.2.5")
        parser._parse(
            ctx,
            changes=CHANGES,
            start_line=START_LINE,
            head_line=HEAD_LINE,
            fix_issue_regex=None,
            fix_issue_repl=None,
        )


def test_parse_single_changes(ctx: Context, parser: Parser):
    CHANGES = dedent(
        f"""\
      {START_LINE}

      ## get-releasenote [1.2.4](https://github.com/No767/get-release/tree/1.2.4) - 2025-12-24

      ### Bug fixes
      
      - Fix links for issues/pull request numbers ([#266])
    """
    )
    ctx.version = parser.find_version(ctx, version_file=None, version="1.2.4")
    ret = parser._parse(
        ctx,
        changes=CHANGES,
        start_line=START_LINE,
        head_line=HEAD_LINE,
        fix_issue_regex=None,
        fix_issue_repl=None,
    )

    assert ret == dedent(
        """\
        ### Bug fixes

        - Fix links for issues/pull request numbers ([#266])"""
    )


def test_parse_multi_changes(ctx: Context, parser: Parser):
    CHANGES = dedent(
        f"""\
      {START_LINE}

    ## get-releasenote [1.1.0](https://github.com/No767/Catherine-Chan/tree/1.1.0) - 2025-12-24

    ### Bug fixes

    - Fix 1 (#266)
    - Fix 4 (#9)

    ### Features

    - Feature 1 (#99)
    """
    )

    ctx.version = parser.find_version(ctx, version_file=None, version="1.1.0")
    ret = parser._parse(
        ctx,
        changes=CHANGES,
        start_line=START_LINE,
        head_line=HEAD_LINE,
        fix_issue_regex=None,
        fix_issue_repl=None,
    )

    assert ret == dedent(
        """\
        ### Bug fixes

        - Fix 1 (#266)
        - Fix 4 (#9)

        ### Features

        - Feature 1 (#99)"""
    )
