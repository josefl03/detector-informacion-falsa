import markitdown
from loguru import logger
import io

class Parser:
    def __init__(self):
        self.markitdown = markitdown.MarkItDown(
            enable_plugins=True,
            enable_builtins=True,
        )
            
    def html_to_md(self, html: str) -> str:
        """
        Convert HTML to Markdown using MarkItdown.
        """
        # Convert the HTML to a fake BinaryIO object
        html_b = io.BytesIO(html.encode("utf-8"))
        
        md = self.markitdown.convert(html_b)
        
        # Remove any line starting with *
        processed_md = ""
        for line in md.markdown.splitlines():
            trimmed_line = line.strip()
            if trimmed_line.startswith("*") or trimmed_line.startswith("+") or trimmed_line.startswith("[!"):
                continue
            
            processed_md += line + "\n"
        
        # Remove duplicate newlines
        processed_md = "\n".join(
            line for line in processed_md.splitlines() if line.strip()
        )
        
        return processed_md.strip()
    
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    
    # Example usage
    parser = Parser()
    with open("dummy/noticia.html", "r") as f:
        html_content = f.read()
    markdown_content = parser.html_to_md(html_content)
    print(markdown_content)  # Output: # Hello World\n\nThis is a test.
    print(f"length: {len(markdown_content)}") # 72812