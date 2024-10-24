# Creating Custom Output Formats

This guide covers how to create custom output formats in dir2text by implementing the `OutputStrategy` interface. Learn how to format directory content in ways that suit your specific needs.

## Basic Implementation

### Simple Text Format

```python
from typing import Optional
from dir2text.output_strategies import OutputStrategy

class SimpleTextStrategy(OutputStrategy):
    def format_start(self, relative_path: str, 
                    file_token_count: Optional[int] = None) -> str:
        header = f"=== {relative_path} ==="
        if file_token_count is not None:
            header += f" ({file_token_count} tokens)"
        return f"{header}\n"
    
    def format_content(self, content: str) -> str:
        return content
    
    def format_end(self, file_token_count: Optional[int] = None) -> str:
        return "\n" + "=" * 40 + "\n"
    
    def get_file_extension(self) -> str:
        return ".txt"

# Usage
from dir2text import FileSystemTree
from dir2text.file_content_printer import FileContentPrinter

fs_tree = FileSystemTree("/path/to/project")
printer = FileContentPrinter(fs_tree, SimpleTextStrategy())
```

### Markdown Format

```python
class MarkdownStrategy(OutputStrategy):
    def format_start(self, relative_path: str, 
                    file_token_count: Optional[int] = None) -> str:
        header = f"## File: {relative_path}\n\n"
        if file_token_count is not None:
            header += f"*Tokens: {file_token_count}*\n\n"
        return f"{header}```\n"
    
    def format_content(self, content: str) -> str:
        return content
    
    def format_end(self, file_token_count: Optional[int] = None) -> str:
        return "```\n\n---\n\n"
    
    def get_file_extension(self) -> str:
        return ".md"
```

## Advanced Implementations

### HTML with Syntax Highlighting

```python
import html
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, TextLexer

class HTMLStrategy(OutputStrategy):
    def __init__(self):
        self.formatter = HtmlFormatter(style='monokai')
        self.current_file = None
        self._write_css = True
    
    def format_start(self, relative_path: str, 
                    file_token_count: Optional[int] = None) -> str:
        self.current_file = relative_path
        result = []
        
        # Add CSS on first file
        if self._write_css:
            result.append(f"<style>{self.formatter.get_style_defs()}</style>")
            self._write_css = False
        
        result.extend([
            '<div class="file-container">',
            f'<h3>{html.escape(relative_path)}</h3>'
        ])
        
        if file_token_count is not None:
            result.append(
                f'<div class="token-count">Tokens: {file_token_count}</div>'
            )
        
        return '\n'.join(result)
    
    def format_content(self, content: str) -> str:
        try:
            lexer = get_lexer_for_filename(self.current_file)
        except:
            lexer = TextLexer()
        
        return highlight(content, lexer, self.formatter)
    
    def format_end(self, file_token_count: Optional[int] = None) -> str:
        return '</div>\n'
    
    def get_file_extension(self) -> str:
        return '.html'
```