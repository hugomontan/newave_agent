"""Script para dividir doc.md em arquivos específicos."""
import re
from pathlib import Path

def split_documentation():
    # Paths
    base_dir = Path(__file__).parent.parent
    doc_path = base_dir / "doc.md"
    specific_dir = base_dir / "docs" / "specific"
    
    specific_dir.mkdir(parents=True, exist_ok=True)
    
    content = doc_path.read_text(encoding="utf-8")
    
    # Pattern to find file sections
    section_pattern = r"^## ([A-Z_]+\.DAT)\s*$"
    
    lines = content.split("\n")
    sections = []
    current_section = None
    current_content = []
    
    for line in lines:
        match = re.match(section_pattern, line, re.MULTILINE)
        if match:
            if current_section and current_content:
                sections.append({
                    "title": current_section,
                    "content": "\n".join(current_content)
                })
            current_section = match.group(1)
            current_content = [line]
        elif current_section:
            current_content.append(line)
    
    if current_section and current_content:
        sections.append({
            "title": current_section,
            "content": "\n".join(current_content)
        })
    
    # Write each section
    for section in sections:
        filename = section["title"].lower().replace(".", "_") + ".md"
        filepath = specific_dir / filename
        
        filepath.write_text(section["content"], encoding="utf-8")
        print(f"Created: {filepath}")
    
    print(f"\nTotal: {len(sections)} files created")

if __name__ == "__main__":
    split_documentation()

