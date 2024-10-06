import os
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


class ExclusionRules:
    def exclude(self, path: str) -> bool:
        raise NotImplementedError


class GitIgnoreExclusionRules(ExclusionRules):
    def __init__(self, rules_file: str):
        if not os.path.exists(rules_file):
            raise FileNotFoundError(f"Rules file not found: {rules_file}")
        with open(rules_file, "r") as f:
            gitignore_content = f.read().splitlines()
        self.spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_content)

    def exclude(self, path: str) -> bool:
        should_exclude = self.spec.match_file(path)
        return should_exclude
