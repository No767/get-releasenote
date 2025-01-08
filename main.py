#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from typing import Optional

import msgspec
from packaging.version import parse as parse_version

VERSION_RE = re.compile(
    "^{version} *= *{spec}".format(
        version="(?:__version__|version)",
        spec=r"""(["'])((?:(?!\1).)*)\1""",
    ),
    re.MULTILINE,
)


class Context(msgspec.Struct):
    root: Path
    version: str = ""

    def read_file(self, name: str) -> str:
        fname = self.root / name
        if not fname.exists():
            raise ValueError(f"file '{name}' doesn't exist")
        return fname.read_text("utf-8")


class Output(msgspec.Struct, frozen=True):
    version: str
    pre_release: bool
    dev_release: bool

    def show(self) -> None:
        print(f"::set-output name=version::{self.version}")
        print(f"::set-output name=prerelease::{str(self.pre_release).lower()}")
        print(f"::set-output name=devrelease::{str(self.dev_release).lower()}")


class Parser:
    """Responsible for parsing changelog changes"""

    def __init__(self, changes_file: str, name: str):
        self.changes_file = changes_file
        self.name = name

    def check_head(self, version: str, head: Optional[str]) -> None:
        if not head:
            return
        pre = "refs/tags/"
        if not head.startswith(pre):
            raise ValueError(f"Git head '{head}' doesn't point at a tag")
        tag = head[len(pre) :]
        if tag != version and tag != "v" + version:
            raise ValueError(f"Git tag '{tag}' mismatches with version '{version}'")

    def check_changes_version(self, declared_version: str, found_version: str) -> None:
        if declared_version == found_version:
            return
        dver = parse_version(declared_version)
        fver = parse_version(found_version)

        if dver < fver:
            raise ValueError(
                f"The distribution version {dver} is older than "
                f"{fver} (from '{self.changes_file}').\n"
                "Hint: push git tag with the latest version."
            )

        else:
            raise ValueError(
                f"The distribution version {dver} is younger than "
                f"{fver} (from '{self.changes_file}').\n"
                "Hint: run 'towncrier' again."
            )

    def find_version(self, ctx: Context, *, version_file: str, version: str) -> str:
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

    def parse(
        self,
        ctx: Context,
        *,
        start_line: str,
        head_line: str,
        fix_issue_regex: str,
        fix_issue_repl: str,
        input_check_ref: str,
    ) -> str:
        if (
            fix_issue_regex
            and not fix_issue_repl
            or not fix_issue_regex
            and fix_issue_repl
        ):
            raise ValueError(
                "fix_issue_regex and fix_issue_repl should be used together"
            )
        self.check_head(ctx.version, input_check_ref)
        changes = ctx.read_file(self.changes_file)

        _, sep, msg = changes.partition(start_line)
        if not sep:
            raise ValueError(
                f"Cannot find TOWNCRIER start mark ({start_line!r}) "
                "in file '{changes_file}'"
            )

        msg = msg.strip()
        head_re = re.compile(
            head_line.format(
                version=r"\[(?P<version>[0-9][0-9.abcr]+(\.post[0-9]+)?)\]",
                date=r"\d+-\d+-\d+",
                name=self.name,
            ),
            re.MULTILINE,
        )
        match = head_re.match(msg)
        if match is None:
            raise ValueError(
                f"Cannot find TOWNCRIER version head mark ({head_re.pattern!r}) "
                f"in file '{self.changes_file}'"
            )
        found_version = match.group("version")
        self.check_changes_version(ctx.version, found_version)

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


class Controller:
    """Main controller for operations"""

    def __init__(self, root: Path):
        self.root = root
        self.ctx = Context(root)
        self.parser = Parser(
            changes_file=os.environ["INPUT_CHANGES_FILE"], name=os.environ["INPUT_NAME"]
        )

    def start(self):
        self.ctx.version = self.parser.find_version(
            self.ctx,
            version_file=os.environ["INPUT_VERSION_FILE"],
            version=os.environ["INPUT_VERSION"],
        )
        version = parse_version(self.ctx.version)

        note = self.parser.parse(
            self.ctx,
            start_line=os.environ["INPUT_START_LINE"],
            head_line=os.environ["INPUT_HEAD_LINE"],
            fix_issue_regex=os.environ["INPUT_FIX_ISSUE_REGEX"],
            fix_issue_repl=os.environ["INPUT_FIX_ISSUE_REPL"],
            input_check_ref=os.environ["INPUT_CHECK_REF"],
        )

        output = Output(
            version=self.ctx.version,
            pre_release=version.is_prerelease,
            dev_release=version.is_devrelease,
        )
        output.show()

        output_file = os.environ["INPUT_OUTPUT_FILE"]
        (self.root / output_file).write_text(note)


def main() -> int:
    controller = Controller(root=Path.cwd())
    controller.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
