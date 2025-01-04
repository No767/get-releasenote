#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from typing import Optional

import msgspec
from packaging.version import parse as parse_version

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class Context(msgspec.Struct):
    root: Path
    version: str = ""

    def read_file(self, name: str) -> str:
        fname = self.root / name
        if not fname.exists():
            raise ValueError(f"file '{name}' doesn't exist")
        return fname.read_text("utf-8")


def parse_changes(
    ctx: Context,
    *,
    changes_file: str,
    start_line: str,
    head_line: str,
    fix_issue_regex: str,
    fix_issue_repl: str,
    name: str,
) -> str:
    check_fix_issue(fix_issue_regex, fix_issue_repl)
    changes = ctx.read_file(changes_file)

    return _parse_changes(
        changes=changes,
        changes_file=changes_file,
        version=ctx.version,
        start_line=start_line,
        head_line=head_line,
        fix_issue_regex=fix_issue_regex,
        fix_issue_repl=fix_issue_repl,
        name=name,
    )


def _parse_changes(
    *,
    changes: str,
    changes_file: str,
    version: str,
    start_line: str,
    head_line: str,
    fix_issue_regex: str,
    fix_issue_repl: str,
    name: str,
) -> str:
    _, sep, msg = changes.partition(start_line)
    if not sep:
        raise ValueError(
            f"Cannot find TOWNCRIER start mark ({start_line!r}) "
            "in file '{changes_file}'"
        )

    msg = msg.strip()
    head_re = re.compile(
        head_line.format(
            version=r"(?P<version>[0-9][0-9.abcr]+(\.post[0-9]+)?)",
            date=r"\d+-\d+-\d+",
            name=name,
        ),
        re.MULTILINE,
    )
    match = head_re.match(msg)
    if match is None:
        raise ValueError(
            f"Cannot find TOWNCRIER version head mark ({head_re.pattern!r}) "
            f"in file '{changes_file}'"
        )
    found_version = match.group("version")
    check_changes_version(version, found_version, changes_file)

    match2 = head_re.search(msg, match.end())
    if match2 is not None:
        # There are older release records
        msg = msg[match.end() : match2.start()]
    else:
        # There is the only release record
        msg = msg[match.end() :]

    if fix_issue_regex:
        msg = re.sub(fix_issue_regex, fix_issue_repl, msg)
    return msg.strip()


def check_changes_version(
    declared_version: str, found_version: str, changes_file: str
) -> None:
    if declared_version == found_version:
        return
    dver = parse_version(declared_version)
    fver = parse_version(found_version)

    if dver < fver:
        raise ValueError(
            f"The distribution version {dver} is older than "
            f"{fver} (from '{changes_file}').\n"
            "Hint: push git tag with the latest version."
        )

    else:
        raise ValueError(
            f"The distribution version {dver} is younger than "
            f"{fver} (from '{changes_file}').\n"
            "Hint: run 'towncrier' again."
        )


VERSION_RE = re.compile(
    "^{version} *= *{spec}".format(
        version="(?:__version__|version)",
        spec=r"""(["'])((?:(?!\1).)*)\1""",
    ),
    re.MULTILINE,
)


def find_version(ctx: Context, version_file: str, version: str) -> str:
    if not version and not version_file:
        raise ValueError("No one of 'version', 'version_file' is set")
    if version:
        if version_file:
            raise ValueError("version and version_file arguments are ambiguous")
        return version
    txt = ctx.read_file(version_file)
    if match := VERSION_RE.search(txt):
        return match.group(2)
    raise ValueError(f"Unable to determine version in file '{version_file}'")


def check_fix_issue(fix_issue_regex: str, fix_issue_repl: str) -> None:
    if fix_issue_regex and not fix_issue_repl or not fix_issue_regex and fix_issue_repl:
        raise ValueError("fix_issue_regex and fix_issue_repl should be used together")


def check_head(version: str, head: Optional[str]) -> None:
    if not head:
        return
    pre = "refs/tags/"
    if not head.startswith(pre):
        raise ValueError(f"Git head '{head}' doesn't point at a tag")
    tag = head[len(pre) :]
    if tag != version and tag != "v" + version:
        raise ValueError(f"Git tag '{tag}' mismatches with version '{version}'")


def main() -> int:
    root = Path.cwd()
    ctx = Context(root)
    ctx.version = find_version(
        ctx,
        os.environ["INPUT_VERSION_FILE"],
        os.environ["INPUT_VERSION"],
    )
    version = parse_version(ctx.version)
    check_head(ctx.version, os.environ["INPUT_CHECK_REF"])
    note = parse_changes(
        ctx,
        changes_file=os.environ["INPUT_CHANGES_FILE"],
        start_line=os.environ["INPUT_START_LINE"],
        head_line=os.environ["INPUT_HEAD_LINE"],
        fix_issue_regex=os.environ["INPUT_FIX_ISSUE_REGEX"],
        fix_issue_repl=os.environ["INPUT_FIX_ISSUE_REPL"],
        name=os.environ["INPUT_NAME"],
    )
    print(f"::set-output name=version::{ctx.version}")
    is_prerelease = version.is_prerelease
    print(f"::set-output name=prerelease::{str(is_prerelease).lower()}")
    is_devrelease = version.is_devrelease
    print(f"::set-output name=devrelease::{str(is_devrelease).lower()}")
    output_file = os.environ["INPUT_OUTPUT_FILE"]
    (root / output_file).write_text(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
