"""
Filter out non-books (research papers, products, profiles) from extracted list
"""

import json
import re

def is_likely_real_book(title: str, link: str = "") -> bool:
    """Determine if an entry is likely a real book vs paper/product/profile"""
    
    title_lower = title.lower()
    
    # REJECT: Research paper indicators
    paper_indicators = [
        'randomized controlled trial',
        'meta-analysis',
        'systematic review',
        'prospective cohort',
        'clinical trial',
        'pilot study',
        'slope differences',
        'evaluation of',
        'effect of',
        'analysis of',
        'impact on health',
        'correlation between',
        'association between',
    ]
    if any(indicator in title_lower for indicator in paper_indicators):
        return False
    
    # REJECT: Sponsor/Product indicators
    product_indicators = [
        'eight sleep', 'ag1', 'betterhelp', 'lmnt', 'insidetracker',
        'momentous', 'clearlyfiltered', 'pitcher', 'lamp', 'shampoo',
        'biotin', 'supplement', 'therapy services', 'masterclass',
        'siena health', 'workout splits',
    ]
    if any(product in title_lower for product in product_indicators):
        return False
    
    # REJECT: Social media / Profile indicators
    profile_indicators = [
        'facebook', 'instagram', 'twitter', 'linkedin', 'x:', 
        'academic profile', 'lab website', 'website:', 'newsletter',
        'other platforms', 'personal website', 'publications:',
        'stanford academic', 'northeastern university',
    ]
    if any(profile in title_lower for profile in profile_indicators):
        return False
    
    # REJECT: Generic/incomplete titles
    generic_indicators = [
        'book links', 'articles', 'books\n', 'resources',
        'general ', 'other resources', 'timestamps',
    ]
    if any(generic in title_lower for generic in generic_indicators):
        return False
    
    # REJECT: Too short (likely fragments)
    if len(title) < 10:
        return False
    
    # REJECT: Ends with colon but nothing after (likely incomplete/section header)
    if title.strip().endswith(':') and len(title) < 50:
        # Exception: Some books have colons in titles
        if not any(word in title_lower for word in ['how', 'why', 'what', 'where']):
            return False
    
    # REJECT: Starts with common non-book prefixes
    non_book_prefixes = [
        'dr. ', 'prof. ', 'episode ', 'link:', 'https://', 'http://',
        'website:', 'podcast:', 'youtube:', 'watch:', 'listen:',
    ]
    if any(title_lower.startswith(prefix) for prefix in non_book_prefixes):
        return False
    
    # ACCEPT: Known good book patterns
    good_patterns = [
        r':\s*(?:the|a|an)\s+\w+',  # "Title: The Subtitle"
        r'how to \w+',               # "How to..." books
        r'why \w+',                  # "Why..." books  
        r'the \w+ (book|guide|way|method|power|science)',
    ]
    for pattern in good_patterns:
        if re.search(pattern, title_lower):
            return True
    
    # ACCEPT: Has typical book title structure
    # Capital first letter, reasonable length, no obvious red flags
    if (title[0].isupper() and 
        len(title) > 15 and 
        len(title) < 150 and
        not title.strip().endswith(':')):
        return True
    
    return False


def clean_book_title(title: str) -> str:
    """Clean up book title (remove trailing colons, etc)"""
    title = title.strip()
    
    # Remove trailing colons that are artifacts
    if title.endswith(':'):
        title = title[:-1].strip()
    
    # Remove "Books\n" prefix if present
    title = re.sub(r'^Books\s*\n\s*', '', title)
    
    # Remove common prefixes
    prefixes = ['Book Links\n', 'Books\n', 'Articles\n']
    for prefix in prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
    
    return title


def filter_books():
    """Filter the extracted books to only real books"""
    
    # Load extracted data
    with open('huberman_books_final.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data['books'])
    
    # Filter books
    real_books = []
    rejected = []
    
    for book in data['books']:
        title = clean_book_title(book['title'])
        
        if is_likely_real_book(title, book['link']):
            book['title'] = title  # Use cleaned title
            real_books.append(book)
        else:
            rejected.append(book)
    
    # Save filtered books
    filtered_data = {
        'total_videos': data['total_videos'],
        'books_found': len(real_books),
        'books': real_books
    }
    
    with open('huberman_books_filtered.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)
    
    # Create clean text list
    with open('huberman_books_clean.txt', 'w', encoding='utf-8') as f:
        f.write("HUBERMAN LAB - REAL BOOKS ONLY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Filtered from {original_count} to {len(real_books)} books\n")
        f.write(f"Removed {len(rejected)} non-books (papers, products, profiles)\n\n")
        f.write("="*80 + "\n\n")
        
        for i, book in enumerate(real_books, 1):
            f.write(f"{i}. {book['title']}\n")
            f.write(f"   Author: {book['author']}\n")
            f.write(f"   Link: {book['link']}\n\n")
    
    # Create clean LaTeX
    create_clean_latex(real_books, 'huberman_books_clean.tex')
    
    # Show what was rejected (for review)
    with open('rejected_entries.txt', 'w', encoding='utf-8') as f:
        f.write("REJECTED ENTRIES (not books)\n")
        f.write("="*80 + "\n\n")
        for i, book in enumerate(rejected, 1):
            f.write(f"{i}. {book['title']}\n")
            f.write(f"   Link: {book['link']}\n\n")
    
    print(f"\n{'='*80}")
    print(f"FILTERING COMPLETE")
    print(f"{'='*80}")
    print(f"Original entries: {original_count}")
    print(f"Real books found: {len(real_books)}")
    print(f"Rejected (papers/products/etc): {len(rejected)}")
    print(f"\nFiles created:")
    print(f"  ✓ huberman_books_filtered.json - Clean data")
    print(f"  ✓ huberman_books_clean.txt - Readable list")
    print(f"  ✓ huberman_books_clean.tex - LaTeX document")
    print(f"  ✓ rejected_entries.txt - Review rejected items")
    print(f"{'='*80}\n")
    
    # Show sample of real books
    print("SAMPLE OF REAL BOOKS FOUND:\n")
    for i, book in enumerate(real_books[:20], 1):
        print(f"{i}. {book['title']}")
    
    if len(real_books) > 20:
        print(f"\n... and {len(real_books) - 20} more")


def create_clean_latex(books, filename):
    """Create clean LaTeX document"""
    def escape_latex(text):
        replacements = {
            '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
            '_': r'\_', '{': r'\{', '}': r'\}',
            '~': r'\textasciitilde{}', '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text
    
    latex = [
        r'\documentclass{article}',
        r'\usepackage[utf8]{inputenc}',
        r'\usepackage{hyperref}',
        r'\usepackage{longtable}',
        r'\usepackage{booktabs}',
        r'\begin{document}',
        r'\section{Huberman Lab - Verified Book Recommendations}',
        '',
        r'\begin{longtable}{|p{8cm}|p{4cm}|p{2.5cm}|}',
        r'\hline',
        r'\textbf{Book Title} & \textbf{Author} & \textbf{Link} \\',
        r'\hline',
    ]
    
    for book in books:
        title = escape_latex(book['title'])
        author = escape_latex(book['author'])
        link = r'\href{' + book['link'] + r'}{Amazon}'
        
        latex.append(f"{title} & {author} & {link} \\\\")
        latex.append(r'\hline')
    
    latex.extend([
        r'\end{longtable}',
        '',
        f"\\textit{{Total books: {len(books)}}}",
        r'\end{document}'
    ])
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex))


if __name__ == "__main__":
    filter_books()
