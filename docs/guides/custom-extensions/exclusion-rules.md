# Creating Custom Exclusion Rules

This guide covers the creation and implementation of custom exclusion rules for dir2text. Learn how to control which files and directories are processed based on your specific needs.

## Basic Implementation

### Size-Based Rule

```python
import os
from typing import List, Union

from dir2text.exclusion_rules.base_rules import BaseExclusionRules

class SizeExclusionRules(BaseExclusionRules):
    def __init__(self, max_size_bytes: int):
        self.max_size = max_size_bytes
    
    def exclude(self, path: str) -> bool:
        try:
            return os.path.isfile(path) and \
                   os.path.getsize(path) > self.max_size
        except OSError:
            return False  # Don't exclude if we can't check size
    
    def load_rules(self, rules_files: Union[str, List[str]]) -> None:
        # Convert to list if it's a single string
        if isinstance(rules_files, str):
            rules_files = [rules_files]
            
        for rules_file in rules_files:
            with open(rules_file) as f:
                # Expect file to contain size in bytes
                size = int(f.read().strip())
                # Take the largest size from multiple files
                if hasattr(self, 'max_size'):
                    self.max_size = max(self.max_size, size)
                else:
                    self.max_size = size

# Usage
rules = SizeExclusionRules(1_000_000)  # 1MB limit
```

### Time-Based Rule

```python
import os
import time
from typing import List, Union

class TimeBasedExclusionRules(BaseExclusionRules):
    def __init__(self, max_age_days: float = 30):
        self.max_age = max_age_days * 86400  # Convert to seconds
        self.reference_time = time.time()
    
    def exclude(self, path: str) -> bool:
        try:
            mtime = os.path.getmtime(path)
            return (self.reference_time - mtime) > self.max_age
        except OSError:
            return False
    
    def load_rules(self, rules_files: Union[str, List[str]]) -> None:
        # Convert to list if it's a single string
        if isinstance(rules_files, str):
            rules_files = [rules_files]
            
        for rules_file in rules_files:
            with open(rules_file) as f:
                days = float(f.read().strip())
                # Use the smallest age (most restrictive) from multiple files
                new_age = days * 86400
                if hasattr(self, 'max_age'):
                    self.max_age = min(self.max_age, new_age)
                else:
                    self.max_age = new_age

# Usage
rules = TimeBasedExclusionRules(30)  # 30 days
```

## Advanced Implementations

### Composite Rules

```python
from typing import List, Union

class CompositeExclusionRules(BaseExclusionRules):
    def __init__(self, rules: List[BaseExclusionRules]):
        self.rules = rules
    
    def exclude(self, path: str) -> bool:
        return any(rule.exclude(path) for rule in self.rules)
    
    def load_rules(self, rules_files: Union[str, List[str]]) -> None:
        # Propagate to all constituent rules
        for rule in self.rules:
            rule.load_rules(rules_files)

# Usage
rules = CompositeExclusionRules([
    SizeExclusionRules(1_000_000),
    TimeBasedExclusionRules(30)
])
```

### Supporting Multiple Rule Files

When implementing custom exclusion rules, it's important to properly handle multiple rule files. Your implementation should:

1. Accept either a single file path or a list of file paths in `load_rules`
2. Process each file according to your rule logic
3. Determine how rules from multiple files interact (e.g., most restrictive wins, last rule wins)

Example pattern for handling multiple files:

```python
def load_rules(self, rules_files: Union[str, List[str]]) -> None:
    # Normalize input to a list
    if isinstance(rules_files, str):
        rules_files = [rules_files]
    
    # Process each file
    for rules_file in rules_files:
        if not os.path.exists(rules_file):
            raise FileNotFoundError(f"Rules file not found: {rules_file}")
        
        # Load and apply rules from this file
        with open(rules_file, 'r') as f:
            # Process the file contents according to your rule logic
            pass  # Your implementation here
```

## Performance Optimization

### Caching Rules

```python
from functools import lru_cache

class CachedExclusionRules(BaseExclusionRules):
    def __init__(self, base_rules: BaseExclusionRules):
        self.base_rules = base_rules
    
    @lru_cache(maxsize=1000)
    def exclude(self, path: str) -> bool:
        return self.base_rules.exclude(path)
    
    def load_rules(self, rules_files: Union[str, List[str]]) -> None:
        self.base_rules.load_rules(rules_files)
        self.exclude.cache_clear()
```

## Best Practices

### 1. Rule Design
- Keep rules focused and single-purpose
- Use composition for complex rules
- Implement clear error handling
- Document rule behavior
- Support multiple rule files

### 2. Performance
- Cache expensive operations
- Optimize pattern matching
- Use fast checks first
- Monitor memory usage

### 3. Error Handling
- Handle file system errors gracefully
- Provide meaningful error messages
- Fail safely (don't exclude on errors)

### 4. Multiple Rule Files
- Define clear precedence rules when combining multiple files
- Document how rules interact when using multiple sources
- Consider order-dependent behavior for negation patterns