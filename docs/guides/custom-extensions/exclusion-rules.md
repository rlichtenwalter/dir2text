# Creating Custom Exclusion Rules

This guide covers the creation and implementation of custom exclusion rules for dir2text. Learn how to control which files and directories are processed based on your specific needs.

## Built-in Rule Types

dir2text includes several built-in exclusion rule types:

- **GitIgnoreExclusionRules**: Pattern-based exclusions using .gitignore syntax
- **SizeExclusionRules**: Size-based exclusions for filtering large files  
- **CompositeExclusionRules**: Combines multiple rule types

You can use these built-in rules or create your own custom implementations.

## Basic Implementation

### Using Built-in Size-Based Rules

```python
from dir2text.exclusion_rules.size_rules import SizeExclusionRules

# Create size rules with human-readable formats
rules = SizeExclusionRules("50MB")     # 50 megabytes
rules = SizeExclusionRules("1.5GB")    # 1.5 gigabytes  
rules = SizeExclusionRules("2GiB")     # 2 gibibytes (binary)
rules = SizeExclusionRules(1048576)    # 1 MiB in bytes

# Use with dir2text
from dir2text import StreamingDir2Text

analyzer = StreamingDir2Text(
    directory="/path/to/project",
    exclusion_rules=rules
)
```

### Custom Size-Based Rule Implementation

If you need custom size behavior, you can implement your own:

```python
import os
from pathlib import Path
from typing import List, Union

from dir2text.exclusion_rules.base_rules import BaseExclusionRules

class CustomSizeRules(BaseExclusionRules):
    def __init__(self, max_size_bytes: int):
        self.max_size = max_size_bytes
    
    def exclude(self, path: str) -> bool:
        try:
            path_obj = Path(path)
            if not path_obj.is_file():
                return False
            return path_obj.stat().st_size > self.max_size
        except OSError:
            return False  # Don't exclude if we can't check size
    
    def load_rules(self, rules_files: Union[str, List[str]]) -> None:
        # Implementation for loading size limits from files
        pass
    
    def add_rule(self, rule: str) -> None:
        # Implementation for adding size rules
        pass

# Usage
rules = CustomSizeRules(1_000_000)  # 1MB limit
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

### Using Built-in Composite Rules

```python
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.exclusion_rules.size_rules import SizeExclusionRules
from dir2text.exclusion_rules.composite_rules import CompositeExclusionRules

# Combine Git exclusions with size limits
git_rules = GitIgnoreExclusionRules(".gitignore")
size_rules = SizeExclusionRules("100MB")

composite = CompositeExclusionRules([git_rules, size_rules])

# Use with dir2text - files excluded by EITHER rule are filtered out
analyzer = StreamingDir2Text(
    directory="/path/to/project", 
    exclusion_rules=composite
)
```

### Custom Composite Rules Implementation

```python
from typing import List, Union
from dir2text.exclusion_rules.base_rules import BaseExclusionRules

class CustomCompositeRules(BaseExclusionRules):
    def __init__(self, rules: List[BaseExclusionRules]):
        if not rules:
            raise ValueError("At least one rule must be provided")
        self.rules = rules
    
    def exclude(self, path: str) -> bool:
        # Returns True if ANY rule matches (logical OR)
        return any(rule.exclude(path) for rule in self.rules)
    
    def load_rules(self, rules_files: Union[str, List[str]]) -> None:
        # Propagate to all constituent rules
        for rule in self.rules:
            rule.load_rules(rules_files)
    
    def add_rule(self, rule: str) -> None:
        # Propagate to all constituent rules  
        for rule_obj in self.rules:
            rule_obj.add_rule(rule)

# Usage - combines multiple rule types
rules = CustomCompositeRules([
    SizeExclusionRules("50MB"),
    TimeBasedExclusionRules(30)  # Your custom time-based rules
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

## API Usage Examples

### Simple Size Filtering

```python
from dir2text import StreamingDir2Text
from dir2text.exclusion_rules.size_rules import SizeExclusionRules

# Filter files larger than 10MB
rules = SizeExclusionRules("10MB")

analyzer = StreamingDir2Text(
    directory="/path/to/project",
    exclusion_rules=rules
)

# Process with size filtering
for line in analyzer.stream_tree():
    print(line, end='')
    
for chunk in analyzer.stream_contents():
    print(chunk, end='')
```

### Combining Git and Size Rules

```python
from dir2text import StreamingDir2Text
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.exclusion_rules.size_rules import SizeExclusionRules
from dir2text.exclusion_rules.composite_rules import CompositeExclusionRules

# Set up individual rules
git_rules = GitIgnoreExclusionRules(".gitignore")
size_rules = SizeExclusionRules("50MB")

# Combine them
composite = CompositeExclusionRules([git_rules, size_rules])

# Use with analyzer
analyzer = StreamingDir2Text(
    directory="/path/to/project",
    exclusion_rules=composite,
    tokenizer_model="gpt-4"  # Optional token counting
)

# Files are excluded if they match Git patterns OR exceed size limit
print(f"Processing {analyzer.file_count} files...")
tree_output = "".join(analyzer.stream_tree())
content_output = "".join(analyzer.stream_contents())
```

### Dynamic Rule Management

```python
from dir2text.exclusion_rules.composite_rules import CompositeExclusionRules
from dir2text.exclusion_rules.size_rules import SizeExclusionRules

# Start with basic size rules
size_rules = SizeExclusionRules("100MB")
composite = CompositeExclusionRules([size_rules])

# Add more rules dynamically
git_rules = GitIgnoreExclusionRules()
git_rules.add_rule("*.tmp")
git_rules.add_rule("build/")

composite.add_rule_object(git_rules)

# Check rule composition
print(f"Composite has {composite.get_rule_count()} rule types")

# Use rules programmatically
test_files = ["large_data.csv", "build/output.js", "src/main.py"]
for file_path in test_files:
    if composite.exclude(file_path):
        print(f"Would exclude: {file_path}")
    else:
        print(f"Would include: {file_path}")
```

### Advanced Configuration

```python
from dir2text import StreamingDir2Text
from dir2text.exclusion_rules.size_rules import SizeExclusionRules

# Configure with multiple parameters
rules = SizeExclusionRules("25MB")

analyzer = StreamingDir2Text(
    directory="/path/to/project",
    exclusion_rules=rules,
    output_format="json",           # JSON output
    tokenizer_model="gpt-4",        # Token counting
    follow_symlinks=True,           # Follow symlinks
    permission_action="warn"        # Warn on permission errors
)

# Get comprehensive metrics
print(f"Directories: {analyzer.directory_count}")  
print(f"Files: {analyzer.file_count}")
print(f"Symlinks: {analyzer.symlink_count}")

# Stream with progress tracking
total_lines = 0
for line in analyzer.stream_tree():
    total_lines += 1
    print(line, end='')

for chunk in analyzer.stream_contents():
    print(chunk, end='')
    
# Final metrics after processing
if analyzer.streaming_complete:
    print(f"Total lines: {analyzer.line_count}")
    print(f"Total characters: {analyzer.character_count}")
    if analyzer.token_count:
        print(f"Total tokens: {analyzer.token_count}")
```