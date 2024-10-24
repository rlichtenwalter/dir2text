# Creating Custom Exclusion Rules

This guide covers the creation and implementation of custom exclusion rules for dir2text. Learn how to control which files and directories are processed based on your specific needs.

## Basic Implementation

### Size-Based Rule

```python
import os

class SizeExclusionRules(BaseExclusionRules):
    def __init__(self, max_size_bytes: int):
        self.max_size = max_size_bytes
    
    def exclude(self, path: str) -> bool:
        try:
            return os.path.isfile(path) and \
                   os.path.getsize(path) > self.max_size
        except OSError:
            return False  # Don't exclude if we can't check size
    
    def load_rules(self, rules_file: str) -> None:
        with open(rules_file) as f:
            # Expect file to contain size in bytes
            self.max_size = int(f.read().strip())

# Usage
rules = SizeExclusionRules(1_000_000)  # 1MB limit
```

### Time-Based Rule

```python
import os
import time

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
    
    def load_rules(self, rules_file: str) -> None:
        with open(rules_file) as f:
            self.max_age = float(f.read().strip()) * 86400

# Usage
rules = TimeBasedExclusionRules(30)  # 30 days
```

## Advanced Implementations

### Composite Rules

```python
from typing import List

class CompositeExclusionRules(BaseExclusionRules):
    def __init__(self, rules: List[BaseExclusionRules]):
        self.rules = rules
    
    def exclude(self, path: str) -> bool:
        return any(rule.exclude(path) for rule in self.rules)
    
    def load_rules(self, rules_file: str) -> None:
        for rule in self.rules:
            rule.load_rules(rules_file)

# Usage
rules = CompositeExclusionRules([
    SizeExclusionRules(1_000_000),
    TimeBasedExclusionRules(30)
])
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
    
    def load_rules(self, rules_file: str) -> None:
        self.base_rules.load_rules(rules_file)
        self.exclude.cache_clear()
```

## Best Practices

### 1. Rule Design
- Keep rules focused and single-purpose
- Use composition for complex rules
- Implement clear error handling
- Document rule behavior

### 2. Performance
- Cache expensive operations
- Optimize pattern matching
- Use fast checks first
- Monitor memory usage

### 3. Error Handling
- Handle file system errors gracefully
- Provide meaningful error messages
- Fail safely (don't exclude on errors)
