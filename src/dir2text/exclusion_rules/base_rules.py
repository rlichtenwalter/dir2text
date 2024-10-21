from abc import ABC, abstractmethod


class BaseExclusionRules(ABC):
    @abstractmethod
    def exclude(self, path: str) -> bool:
        """
        Determine if a given path should be excluded.

        Args:
            path (str): The path to check for exclusion.

        Returns:
            bool: True if the path should be excluded, False otherwise.
        """
        pass

    @abstractmethod
    def load_rules(self, rules_file: str) -> None:
        """
        Load exclusion rules from a file.

        Args:
            rules_file (str): Path to the file containing exclusion rules.

        Raises:
            FileNotFoundError: If the rules file does not exist.
        """
        pass
