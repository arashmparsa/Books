"""
Interactive Book Merger for LaTeX Reading List
Merges extracted YouTube books into existing LaTeX document with user approval
"""

import re
import json
from typing import List, Dict, Set
import os

class LaTeXBookMerger:
    def __init__(self, existing_tex_file: str):
        self.existing_tex_file = existing_tex_file
        self.existing_content = ""
        self.existing_books = set()
        
    def load_existing_document(self):
        """Load the existing LaTeX document and parse existing books"""
        with open(self.existing_tex_file, 'r', encoding='utf-8') as f:
            self.existing_content = f.read()
        
        # Parse existing books to avoid duplicates
        self.existing_books = self._parse_existing_books()
        print(f"Found {len(self.existing_books)} existing books in document")
    
    def _parse_existing_books(self) -> Set[str]:
        """Extract book titles from existing LaTeX document"""
        books = set()
        
        # Pattern to match \bookentry commands
        patterns = [
            r'\\bookentry(?:\[[^\]]*\])?\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}',
            r'\\bookentry\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.existing_content)
            for match in matches:
                if isinstance(match, tuple):
                    title = match[0].strip()
                else:
                    title = match.strip()
                books.add(title.lower())
        
        return books
    
    def interactive_merge(self, extracted_books: List[Dict]) -> List[Dict]:
        """Interactively select which books to merge"""
        print(f"\n{'='*80}")
        print("INTERACTIVE BOOK SELECTION")
        print(f"{'='*80}")
        
        selected_books = []
        duplicate_count = 0
        
        for i, book in enumerate(extracted_books, 1):
            title_lower = book['title'].lower()
            
            # Check if book already exists
            if title_lower in self.existing_books:
                print(f"⏩ SKIPPED (duplicate): {book['title']}")
                duplicate_count += 1
                continue
            
            # Present book for approval
            print(f"\n[{i}/{len(extracted_books)}] NEW BOOK FOUND:")
            print(f"   Title:  {book['title']}")
            print(f"   Author: {book['author']}")
            print(f"   Source: {book.get('source_video', 'Huberman Lab Podcast')}")
            
            while True:
                response = input("\nAdd this book? (y)es/(n)o/(s)kip remaining: ").lower().strip()
                if response in ['y', 'yes']:
                    # Get reading status
                    status = self._get_reading_status()
                    book['status'] = status
                    selected_books.append(book)
                    print("✓ ADDED")
                    break
                elif response in ['n', 'no']:
                    print("✗ SKIPPED")
                    break
                elif response in ['s', 'skip']:
                    print("⏭️  SKIPPING REMAINING BOOKS")
                    return selected_books
                else:
                    print("Please enter 'y', 'n', or 's'")
        
        print(f"\n{'='*80}")
        print(f"SELECTION COMPLETE")
        print(f"{'='*80}")
        print(f"Total extracted: {len(extracted_books)}")
        print(f"Duplicates found: {duplicate_count}")
        print(f"New books selected: {len(selected_books)}")
        print(f"Books rejected: {len(extracted_books) - duplicate_count - len(selected_books)}")
        
        return selected_books
    
    def _get_reading_status(self) -> str:
        """Get reading status from user"""
        while True:
            status = input("Reading status? (f)inished/(p)rogress/(t)o read [default: t]: ").lower().strip()
            if status in ['f', 'finished']:
                return 'f'
            elif status in ['p', 'progress']:
                return 'p'
            elif status in ['t', 'to read', '']:
                return 't'
            else:
                print("Please enter 'f', 'p', or 't' (or press Enter for 'to read')")
    
    def merge_into_latex(self, selected_books: List[Dict], output_file: str = None):
        """Merge selected books into LaTeX document"""
        if not output_file:
            base_name = os.path.splitext(self.existing_tex_file)[0]
            output_file = f"{base_name}_merged.tex"
        
        # Sort books alphabetically by title
        selected_books.sort(key=lambda x: x['title'].lower())
        
        # Generate LaTeX for new books
        new_books_latex = self._generate_books_latex(selected_books)
        
        # Find the Huberman Lab section and replace it
        merged_content = self._replace_huberman_section(new_books_latex)
        
        # Write merged document
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        
        print(f"\n✓ MERGED DOCUMENT SAVED: {output_file}")
        return output_file
    
    def _generate_books_latex(self, books: List[Dict]) -> str:
        """Generate LaTeX code for books"""
        latex_lines = []
        
        for book in books:
            title = self._escape_latex(book['title'])
            author = self._escape_latex(book['author'])
            status = book.get('status', 't')  # Default to 'to read'
            
            # Use empty year and source info
            year = ""
            source = "Extracted from Huberman Lab podcast"
            
            latex_lines.append(f"\\bookentry[{status}]{{{title}}}{{{author}}}{{{year}}}{{{source}}}")
        
        return '\n'.join(latex_lines)
    
    def _replace_huberman_section(self, new_books_latex: str) -> str:
        """Replace the Huberman Lab section with updated content"""
        # Pattern to find the Huberman Lab subsection
        huberman_pattern = r'(\\subsection\{Books from Huberman Lab Podcast\}[^{]*\\begin\{itemize\})(.*?)(\\end\{itemize\})'
        
        replacement = f"\\1\n{new_books_latex}\n\\3"
        
        # If the section doesn't exist, create it
        if not re.search(huberman_pattern, self.existing_content, re.DOTALL):
            print("⚠️  Huberman Lab section not found, creating new section...")
            return self._create_huberman_section(new_books_latex)
        
        return re.sub(huberman_pattern, replacement, self.existing_content, flags=re.DOTALL)
    
    def _create_huberman_section(self, new_books_latex: str) -> str:
        """Create Huberman Lab section if it doesn't exist"""
        new_section = f"""
%=============================================================================
\\subsection{{Books from Huberman Lab Podcast}}

\\begin{{item}}
{new_books_latex}
\\end{{item}}
"""
        
        # Find the "To Be Integrated" section and insert before it
        integration_pattern = r'(\\section\{To Be Integrated: Books from YouTube Channels\})'
        if re.search(integration_pattern, self.existing_content):
            return re.sub(integration_pattern, new_section + r'\1', self.existing_content)
        else:
            # Insert before appendices
            appendix_pattern = r'(\\appendix)'
            if re.search(appendix_pattern, self.existing_content):
                return re.sub(appendix_pattern, new_section + r'\1', self.existing_content)
            else:
                # Insert at the end before \end{document}
                return self.existing_content.replace(
                    r'\end{document}',
                    new_section + '\n' + r'\end{document}'
                )
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""
        replacements = {
            '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
            '_': r'\_', '{': r'\{', '}': r'\}',
            '~': r'\textasciitilde{}', '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text
    
    def export_selection_report(self, extracted_books: List[Dict], selected_books: List[Dict], filename: str):
        """Export a report of the selection process"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("BOOK SELECTION REPORT - HUBERMAN LAB\n")
            f.write("="*80 + "\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"Total books extracted: {len(extracted_books)}\n")
            f.write(f"Books selected for merge: {len(selected_books)}\n")
            f.write(f"Duplicate books found: {len([b for b in extracted_books if b['title'].lower() in self.existing_books])}\n")
            f.write(f"Books rejected: {len(extracted_books) - len(selected_books) - len([b for b in extracted_books if b['title'].lower() in self.existing_books])}\n\n")
            
            f.write("SELECTED BOOKS:\n")
            f.write("-"*40 + "\n")
            for book in selected_books:
                status_map = {'f': 'FINISHED', 'p': 'IN PROGRESS', 't': 'TO READ'}
                status = status_map.get(book.get('status', 't'), 'TO READ')
                f.write(f"✓ {status}: {book['title']}\n")
                f.write(f"  Author: {book['author']}\n\n")
            
            f.write("\nALL EXTRACTED BOOKS:\n")
            f.write("-"*40 + "\n")
            for book in extracted_books:
                if book['title'].lower() in self.existing_books:
                    f.write(f"⏩ DUPLICATE: {book['title']}\n")
                elif book in selected_books:
                    f.write(f"✓ SELECTED: {book['title']}\n")
                else:
                    f.write(f"✗ REJECTED: {book['title']}\n")
        
        print(f"✓ SELECTION REPORT: {filename}")


def load_extracted_books(extracted_file: str = "huberman_books_filtered.json") -> List[Dict]:
    """Load books from extraction output"""
    try:
        with open(extracted_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('books', [])
    except FileNotFoundError:
        print(f"❌ Error: {extracted_file} not found.")
        print("Please run the extraction script first.")
        return []


def main():
    # Configuration
    EXISTING_TEX_FILE = "Comprehensive_Reading_List.tex"  # Your main LaTeX file
    EXTRACTED_BOOKS_FILE = "huberman_books_filtered.json"  # Output from extraction
    
    print("\n" + "="*80)
    print("LATEX BOOK MERGER - HUBERMAN LAB")
    print("="*80 + "\n")
    
    # Load extracted books
    print("📚 Loading extracted books...")
    extracted_books = load_extracted_books(EXTRACTED_BOOKS_FILE)
    if not extracted_books:
        return
    
    print(f"✓ Loaded {len(extracted_books)} books from extraction\n")
    
    # Initialize merger
    merger = LaTeXBookMerger(EXISTING_TEX_FILE)
    merger.load_existing_document()
    
    # Interactive selection
    selected_books = merger.interactive_merge(extracted_books)
    
    if not selected_books:
        print("\n❌ No books selected for merging.")
        return
    
    # Merge into LaTeX
    print(f"\n🔄 Merging {len(selected_books)} books into LaTeX document...")
    output_file = merger.merge_into_latex(selected_books)
    
    # Generate report
    merger.export_selection_report(extracted_books, selected_books, "book_merge_report.txt")
    
    print(f"\n{'='*80}")
    print("MERGE COMPLETE!")
    print(f"{'='*80}")
    print(f"📄 Original file: {EXISTING_TEX_FILE}")
    print(f"📄 Merged file: {output_file}")
    print(f"📊 Selection report: book_merge_report.txt")
    print(f"\nNext steps:")
    print(f"1. Review {output_file}")
    print(f"2. Compile with LaTeX to see the updated reading list")
    print(f"3. Manually add publication years if desired")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()