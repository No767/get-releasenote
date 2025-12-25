#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from typing import Optional

import msgspec
from dotenv import dotenv_values, find_dotenv
from packaging.version import parse as parse_version

ENV_VAR_LIST = [
    "INPUT_CHANGES_FILE",
    "INPUT_OUTPUT_FILE",
    "INPUT_CHECK_REF",
    "INPUT_NAME",
    "INPUT_VERSION",
    "INPUT_VERSION_FILE",
    "INPUT_START_LINE",
    "INPUT_HEAD_LINE",
    "INPUT_FIX_ISSUE_REGEX",
    "INPUT_FIX_ISSUE_REPL",
]

VERSION_RE = re.compile(
    "^{version} *= *{spec}".format(
        version="(?:__version__|version)",
        spec=r"""(["'])((?:(?!\1).)*)\1""",
    ),
    re.MULTILINE,
)


class ActionInputs(msgspec.Struct, frozen=True):
    name: str
    version: Optional[str]
    version_file: Optional[str]
    changes_file: str
    output_file: str
    check_ref: Optional[str]
    fix_issue_regex: Optional[str]
    fix_issue_repl: Optional[str]
    start_line: str = "<!-- towncrier release notes start -->"
    head_line: str = r"##\s{name}\s\[{version}\]\(.*\)[\s-]*({date})"


class Context(msgspec.Struct):
    root: Path
    version: Optional[str] = None

    def read_file(self, name: str) -> str:
        self.root = Path(os.environ.get("GITHUB_WORKSPACE", "."))
        fname = self.root / name
        if not fname.exists():
            msg = f"file '{name}' doesn't exist (Path: {fname})"
            raise ValueError(msg)
        return fname.read_text("utf-8")


class Output(msgspec.Struct, frozen=True):
    version: str

    def show(self) -> None:
        is_pre_release = parse_version(self.version).is_prerelease
        is_dev_release = parse_version(self.version).is_devrelease

        with Path.open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            print(f"version={self.version}", file=fh)
            print(f"prerelease={str(is_pre_release).lower()}", file=fh)
            print(f"devrelease={str(is_dev_release).lower()}", file=fh)


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
            msg = f"Git head '{head}' doesn't point at a tag"
            raise ValueError(msg)
        tag = head[len(pre) :]
        if tag != version and tag != "v" + version:
            msg = f"Git tag '{tag}' mismatches with version '{version}'"
            raise ValueError(msg)

    def check_changes_version(self, declared_version: str, found_version: str) -> None:
        if declared_version == found_version:
            return
        dver = parse_version(declared_version)
        fver = parse_version(found_version)

        if dver < fver:
            msg = (
                f"The distribution version {dver} is older than "
                f"{fver} (from '{self.changes_file}').\n"
                "Hint: push git tag with the latest version."
            )
            raise ValueError(msg)

        msg = (
            f"The distribution version {dver} is younger than "
            f"{fver} (from '{self.changes_file}').\n"
            "Hint: run 'towncrier' again."
        )
        raise ValueError(msg)

    def find_version(
        self, ctx: Context, *, version_file: Optional[str], version: Optional[str]
    ) -> str:
        if version is not None:
            return version

        if version_file is not None:
            txt = ctx.read_file(version_file)
            if match := VERSION_RE.search(txt):
                return match.group(2)

        msg = f"Unable to determine version in file '{version_file}'"
        raise ValueError(msg)

    def parse(
        self,
        ctx: Context,
        *,
        start_line: str,
        head_line: str,
        fix_issue_regex: Optional[str],
        fix_issue_repl: Optional[str],
    ) -> str:
        if (fix_issue_regex and not fix_issue_repl) or (
            not fix_issue_regex and fix_issue_repl
        ):
            raise ValueError(
                "fix_issue_regex and fix_issue_repl should be used together"
            )

        if not ctx.version:
            raise ValueError("Version failed to set when finding version")

        changes = ctx.read_file(self.changes_file)

        _, sep, msg = changes.partition(start_line)
        if not sep:
            msg = (
                f"Cannot find TOWNCRIER start mark ({start_line!r}) "
                "in file '{changes_file}'"
            )
            raise ValueError(msg)

        msg = msg.strip()
        head_re = re.compile(
            head_line.format(
                version=r"(?P<version>[0-9][0-9.abcr]+(\.post[0-9]+)?)",
                date=r"\d+-\d+-\d+",
                name=re.escape(self.name) if self.name else ".*",
            ),
            re.MULTILINE,
        )

        match = head_re.match(msg)
        if match is None:
            msg = (
                f"Cannot find TOWNCRIER version head mark ({head_re.pattern!r}) "
                f"in file '{self.changes_file}'"
            )
            raise ValueError(msg)
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
            msg = re.sub(fix_issue_regex, fix_issue_repl or "", msg)
        return msg.strip()


def sanitize_input(env_input: dict[str, str]) -> dict[str, Optional[str]]:
    def _clean(value: str) -> Optional[str]:
        if len(value) == 0:
            return None

        return value

    return {k.removeprefix("INPUT_").lower(): _clean(v) for k, v in env_input.items()}


def main() -> int:
    # This is done as the .env follows GitHub actions's weird standard
    # If a value is not specified, it becomes a blank string
    env_inputs: dict[str, str] = (
        {key: value for key, value in dict(os.environ).items() if key in ENV_VAR_LIST}
        if not find_dotenv()
        else dotenv_values(find_dotenv())
    )  # type: ignore

    root = Path(os.environ.get("GITHUB_WORKSPACE", "."))

    sanitized_input = sanitize_input(env_inputs)
    action_inputs = ActionInputs(**sanitized_input)
    parser = Parser(changes_file=action_inputs.changes_file, name=action_inputs.name)

    ctx = Context(root=root)
    ctx.version = parser.find_version(
        ctx, version_file=action_inputs.version_file, version=action_inputs.version
    )

    note = parser.parse(
        ctx,
        start_line=action_inputs.start_line,
        head_line=action_inputs.head_line,
        fix_issue_regex=action_inputs.fix_issue_regex,
        fix_issue_repl=action_inputs.fix_issue_repl,
    )

    output_file = root / action_inputs.output_file
    output_file.write_text(note)

    if os.environ.get("GITHUB_OUTPUT"):
        output = Output(version=ctx.version)
        output.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())
