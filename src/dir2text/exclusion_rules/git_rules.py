import os

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern  # type: ignore

from .base_rules import BaseExclusionRules


class GitIgnoreExclusionRules(BaseExclusionRules):
    def __init__(self, rules_file: str):
        self.spec: PathSpec
        self.load_rules(rules_file)

    def exclude(self, path: str) -> bool:
        return self.spec.match_file(path)

    def load_rules(self, rules_file: str) -> None:
        if not os.path.exists(rules_file):
            raise FileNotFoundError(f"Rules file not found: {rules_file}")
        with open(rules_file, "r") as f:
            gitignore_content = f.read().splitlines()
        self.spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_content)
