"""
YouTube Channel Book Extractor and Merger
Extracts books from multiple sources and merges into LaTeX
"""

import re
import csv
import os
import requests
from typing import List, Dict, Set, Optional
from urllib.parse import urlparse, parse_qs

class YouTubeBookExtractor:
    def __init__(self, tex_file: str = "_merged.tex", subscriptions_file: str = "subscriptions.csv"):
        self.tex_file = tex_file
        self.subscriptions_file = subscriptions_file
        self.existing_content = ""
        self.existing_books = set()
        self.channels = {}
        
    def load_document(self):
        """Load the LaTeX document and parse existing books"""
        try:
            with open(self.tex_file, 'r', encoding='utf-8') as f:
                self.existing_content = f.read()
            
            self.existing_books = self._parse_existing_books()
            print(f"✓ Loaded {len(self.existing_books)} existing books from {self.tex_file}")
            return True
        except FileNotFoundError:
            print(f"❌ Error: {self.tex_file} not found.")
            return False
    
    def load_subscriptions(self):
        """Load YouTube channel subscriptions from CSV"""
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    channel_id = row['Channel Id']
                    self.channels[channel_id] = {
                        'title': row['Channel Title'],
                        'url': row['Channel Url']
                    }
            print(f"✓ Loaded {len(self.channels)} channels from subscriptions")
            return True
        except FileNotFoundError:
            print(f"❌ Error: {self.subscriptions_file} not found")
            return False
    
    def _parse_existing_books(self) -> Set[str]:
        """Extract book titles from LaTeX document"""
        books = set()
        pattern = r'\\bookentry(?:\[[^\]]*\])?\{([^}]+)\}'
        matches = re.findall(pattern, self.existing_content)
        for title in matches:
            books.add(title.strip().lower())
        return books
    
    def discover_potential_sources(self):
        """Discover potential sources for book data"""
        sources = {
            'text_files': [],
            'csv_files': [],
            'other_files': []
        }
        
        for filename in os.listdir('.'):
            if filename.endswith('.txt'):
                sources['text_files'].append(filename)
            elif filename.endswith('.csv') and filename != self.subscriptions_file:
                sources['csv_files'].append(filename)
            elif any(ext in filename.lower() for ext in ['book', 'reading', 'recommend']):
                sources['other_files'].append(filename)
        
        return sources
    
    def extract_books_from_text_file(self, filename: str, channel_name: str = "Unknown Channel") -> List[Dict]:
        """Extract books from a text file using various patterns"""
        books = []
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Try different patterns to extract books
            patterns = [
                # Pattern: "Title" by Author
                r'"([^"]+)"\s+by\s+([^\n]+)',
                # Pattern: Title - Author
                r'([^-]+?)\s*-\s*([^\n]+)',
                # Pattern: Title by Author
                r'([^:]+?)\s+by\s+([^\n]+)',
                # Just titles (one per line)
                r'^\s*([A-Za-z][^\n]{5,100})$'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        title, author = match[0].strip(), match[1].strip()
                    else:
                        title, author = match.strip(), "Unknown"
                    
                    if self._is_valid_book_title(title):
                        books.append({
                            'title': title,
                            'author': author,
                            'channel': channel_name,
                            'source': filename
                        })
            
            print(f"✓ Extracted {len(books)} books from {filename}")
            return books
            
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            return []
    
    def _is_valid_book_title(self, title: str) -> bool:
        """Check if a title looks like a real book"""
        if not title or len(title) < 5 or len(title) > 200:
            return False
        
        title_lower = title.lower()
        
        # Reject obvious non-books
        reject_patterns = [
            'http://', 'https://', 'www.', '.com', '.org',
            'subscribe', 'follow', 'like', 'share', 'click here',
            'chapter', 'section', 'page', 'copyright'
        ]
        
        if any(pattern in title_lower for pattern in reject_patterns):
            return False
        
        # Must contain alphabetic characters
        if not re.search(r'[a-zA-Z]', title):
            return False
        
        return True
    
    def interactive_channel_selection(self):
        """Let user select which channels to process"""
        print(f"\n{'='*80}")
        print("CHANNEL SELECTION")
        print(f"{'='*80}")
        
        channel_list = list(self.channels.items())
        selected_channels = []
        
        print(f"Found {len(channel_list)} channels in subscriptions")
        
        for i, (channel_id, channel_info) in enumerate(channel_list, 1):
            print(f"\n[{i}] {channel_info['title']}")
            print(f"    ID: {channel_id}")
            
            while True:
                response = input(f"Process this channel? (y)es/(n)o/(s)kip remaining/(a)dd all: ").lower().strip()
                
                if response in ['y', 'yes']:
                    selected_channels.append((channel_id, channel_info))
                    print("✓ SELECTED")
                    break
                elif response in ['n', 'no']:
                    print("✗ SKIPPED")
                    break
                elif response in ['s', 'skip']:
                    print("⏭️ SKIPPING REMAINING")
                    return selected_channels
                elif response in ['a', 'add all']:
                    print("✅ ADDING ALL REMAINING CHANNELS")
                    selected_channels.extend(channel_list[i-1:])
                    return selected_channels
                else:
                    print("Please enter: y/yes, n/no, s/skip, or a/add all")
        
        return selected_channels
    
    def manual_book_entry(self, channel_info: Dict) -> List[Dict]:
        """Manual entry of books for a channel"""
        books = []
        channel_name = channel_info['title']
        
        print(f"\n{'='*50}")
        print(f"MANUAL BOOK ENTRY: {channel_name}")
        print(f"{'='*50}")
        
        while True:
            print(f"\nCurrent books for {channel_name}: {len(books)}")
            print("Enter book information (or 'done' to finish):")
            
            title = input("Book Title: ").strip()
            if title.lower() in ['done', 'quit', 'exit', '']:
                break
            
            author = input("Author: ").strip() or "Unknown"
            
            if title and self._is_valid_book_title(title):
                books.append({
                    'title': title,
                    'author': author,
                    'channel': channel_name,
                    'channel_url': channel_info.get('url', ''),
                    'source': 'manual_entry'
                })
                print("✓ BOOK ADDED")
            else:
                print("❌ Invalid book title")
            
            continue_entry = input("Add another book? (y/n): ").lower().strip()
            if continue_entry not in ['y', 'yes']:
                break
        
        return books
    
    def search_common_books_by_topic(self, channel_title: str) -> List[Dict]:
        """Suggest common books based on channel topic"""
        topic_keywords = self._extract_topic_from_channel(channel_title)
        suggested_books = []
        
        # Common book recommendations by topic
        topic_books = {
            'programming': [
                {"title": "Clean Code", "author": "Robert C. Martin"},
                {"title": "The Pragmatic Programmer", "author": "Andrew Hunt, David Thomas"},
                {"title": "Design Patterns", "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides"},
                {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein"},
                {"title": "Structure and Interpretation of Computer Programs", "author": "Harold Abelson, Gerald Jay Sussman"}
            ],
            'science': [
                {"title": "A Brief History of Time", "author": "Stephen Hawking"},
                {"title": "The Selfish Gene", "author": "Richard Dawkins"},
                {"title": "Cosmos", "author": "Carl Sagan"},
                {"title": "The Double Helix", "author": "James D. Watson"},
                {"title": "The Elegant Universe", "author": "Brian Greene"}
            ],
            'mathematics': [
                {"title": "Principles of Mathematical Analysis", "author": "Walter Rudin"},
                {"title": "Linear Algebra Done Right", "author": "Sheldon Axler"},
                {"title": "Introduction to Linear Algebra", "author": "Gilbert Strang"},
                {"title": "How to Solve It", "author": "George Pólya"},
                {"title": "Gödel, Escher, Bach", "author": "Douglas Hofstadter"}
            ],
            'history': [
                {"title": "Guns, Germs, and Steel", "author": "Jared Diamond"},
                {"title": "A People's History of the United States", "author": "Howard Zinn"},
                {"title": "The Silk Roads", "author": "Peter Frankopan"},
                {"title": "Sapiens", "author": "Yuval Noah Harari"},
                {"title": "The History of the Ancient World", "author": "Susan Wise Bauer"}
            ],
            'business': [
                {"title": "The Lean Startup", "author": "Eric Ries"},
                {"title": "Zero to One", "author": "Peter Thiel"},
                {"title": "Good to Great", "author": "Jim Collins"},
                {"title": "The Innovator's Dilemma", "author": "Clayton Christensen"},
                {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman"}
            ]
        }
        
        for topic, books_list in topic_books.items():
            if any(keyword in channel_title.lower() for keyword in topic.split('_')):
                suggested_books.extend(books_list)
        
        # Add channel-specific suggestions
        if any(keyword in channel_title.lower() for keyword in ['huberman', 'lab', 'neuroscience']):
            suggested_books.extend([
                {"title": "The Brain That Changes Itself", "author": "Norman Doidge"},
                {"title": "Behave", "author": "Robert Sapolsky"},
                {"title": "The Tell-Tale Brain", "author": "V.S. Ramachandran"},
                {"title": "Principles of Neural Science", "author": "Eric R. Kandel"}
            ])
        
        return suggested_books
    
    def _extract_topic_from_channel(self, channel_title: str) -> List[str]:
        """Extract topic keywords from channel title"""
        topics = []
        channel_lower = channel_title.lower()
        
        topic_mappings = {
            'programming': ['code', 'programming', 'developer', 'software', 'computer science'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'research'],
            'mathematics': ['math', 'mathematics', 'algebra', 'calculus'],
            'history': ['history', 'historical', 'archaeology'],
            'business': ['business', 'entrepreneur', 'startup', 'marketing'],
            'technology': ['tech', 'technology', 'engineering', 'maker'],
            'education': ['education', 'learn', 'teaching', 'tutorial'],
            'health': ['health', 'fitness', 'medicine', 'wellness']
        }
        
        for topic, keywords in topic_mappings.items():
            if any(keyword in channel_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['general']
    
    def interactive_book_discovery(self, selected_channels: List) -> List[Dict]:
        """Interactive process to discover books for selected channels"""
        all_books = []
        
        print(f"\n{'='*80}")
        print("BOOK DISCOVERY PROCESS")
        print(f"{'='*80}")
        
        # First, discover any existing text/csv files
        sources = self.discover_potential_sources()
        
        if sources['text_files']:
            print(f"\nFound text files: {sources['text_files']}")
            for text_file in sources['text_files']:
                use_file = input(f"Extract books from {text_file}? (y/n): ").lower().strip()
                if use_file in ['y', 'yes']:
                    # Try to match with channels
                    for channel_id, channel_info in selected_channels:
                        if channel_info['title'].lower() in text_file.lower():
                            books = self.extract_books_from_text_file(text_file, channel_info['title'])
                            all_books.extend(books)
                            break
                    else:
                        # Use for all channels or specific channel?
                        books = self.extract_books_from_text_file(text_file, "Multiple Channels")
                        all_books.extend(books)
        
        # Process each selected channel
        for channel_id, channel_info in selected_channels:
            channel_books = self.process_single_channel(channel_info)
            all_books.extend(channel_books)
        
        return all_books
    
    def process_single_channel(self, channel_info: Dict) -> List[Dict]:
        """Process a single channel for book discovery"""
        channel_name = channel_info['title']
        books = []
        
        print(f"\n{'='*60}")
        print(f"PROCESSING: {channel_name}")
        print(f"{'='*60}")
        
        # Option 1: Suggest common books by topic
        suggested_books = self.search_common_books_by_topic(channel_name)
        if suggested_books:
            print(f"\n📚 Suggested books for '{channel_name}':")
            for i, book in enumerate(suggested_books, 1):
                print(f"   {i}. {book['title']} by {book['author']}")
            
            add_suggested = input("\nAdd suggested books? (y/n/all): ").lower().strip()
            if add_suggested in ['y', 'yes', 'all']:
                if add_suggested == 'all':
                    for book in suggested_books:
                        book['channel'] = channel_name
                        book['channel_url'] = channel_info.get('url', '')
                        book['source'] = 'topic_suggestion'
                        books.append(book)
                    print("✅ ADDED ALL SUGGESTED BOOKS")
                else:
                    for i, book in enumerate(suggested_books, 1):
                        add_book = input(f"Add '{book['title']}'? (y/n): ").lower().strip()
                        if add_book in ['y', 'yes']:
                            book['channel'] = channel_name
                            book['channel_url'] = channel_info.get('url', '')
                            book['source'] = 'topic_suggestion'
                            books.append(book)
                            print("✓ ADDED")
        
        # Option 2: Manual entry
        manual_books = self.manual_book_entry(channel_info)
        books.extend(manual_books)
        
        print(f"\n✓ Completed {channel_name}: {len(books)} books")
        return books
    
    def interactive_selection(self, all_books: List[Dict]) -> List[Dict]:
        """Interactive book selection with filtering"""
        print(f"\n{'='*80}")
        print("FINAL BOOK SELECTION")
        print(f"{'='*80}")
        
        selected_books = []
        duplicate_count = 0
        
        for i, book in enumerate(all_books, 1):
            title_lower = book['title'].lower()
            
            # Skip duplicates
            if title_lower in self.existing_books:
                print(f"⏩ SKIPPED (duplicate): {book['title']}")
                duplicate_count += 1
                continue
            
            # Show book info
            print(f"\n[{i}/{len(all_books)}] {book['title']}")
            print(f"   Author: {book['author']}")
            print(f"   Channel: {book['channel']}")
            print(f"   Source: {book.get('source', 'unknown')}")
            
            while True:
                response = input("\nAdd this book? (y)es/(n)o/(s)kip remaining/(a)dd all remaining: ").lower().strip()
                
                if response in ['y', 'yes']:
                    status = self._get_reading_status()
                    book['status'] = status
                    selected_books.append(book)
                    print("✓ ADDED")
                    break
                elif response in ['n', 'no']:
                    print("✗ SKIPPED")
                    break
                elif response in ['s', 'skip']:
                    print("⏭️ SKIPPING REMAINING")
                    return selected_books
                elif response in ['a', 'add all']:
                    print("✅ ADDING ALL REMAINING")
                    for remaining in all_books[i-1:]:
                        if remaining['title'].lower() not in self.existing_books:
                            remaining['status'] = 't'
                            selected_books.append(remaining)
                    return selected_books
                else:
                    print("Please enter: y/yes, n/no, s/skip, or a/add all")
        
        print(f"\nSelection complete: {len(selected_books)} new books selected")
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
                print("Please enter 'f', 'p', or 't'")
    
    def merge_books(self, selected_books: List[Dict]):
        """Merge selected books into LaTeX document"""
        if not selected_books:
            print("❌ No books selected for merging.")
            return
        
        # Group books by channel
        books_by_channel = {}
        for book in selected_books:
            channel = book['channel']
            if channel not in books_by_channel:
                books_by_channel[channel] = []
            books_by_channel[channel].append(book)
        
        # Generate LaTeX entries
        new_books_latex = self._generate_latex_entries(books_by_channel)
        
        # Insert into document
        success = self._insert_into_document(new_books_latex)
        
        if success:
            print(f"✓ Successfully merged {len(selected_books)} books into {self.tex_file}")
            self._create_selection_report(selected_books, books_by_channel)
        else:
            print("❌ Failed to merge books into document")
    
    def _generate_latex_entries(self, books_by_channel: Dict) -> str:
        """Generate LaTeX entries grouped by channel"""
        latex_sections = []
        
        for channel, books in books_by_channel.items():
            # Sort books alphabetically
            books.sort(key=lambda x: x['title'].lower())
            
            channel_entries = []
            for book in books:
                title = self._escape_latex(book['title'])
                author = self._escape_latex(book['author'])
                status = book.get('status', 't')
                year = book.get('year', '')
                
                channel_entries.append(f"\\bookentry[{status}]{{{title}}}{{{author}}}{{{year}}}{{Recommended by {channel}}}")
            
            # Create section for this channel
            channel_section = "% " + "="*50 + f"\n% Books from {channel}\n% " + "="*50 + "\n" + "\n".join(channel_entries)
            latex_sections.append(channel_section)
        
        return "\n\n".join(latex_sections)
    
    def _insert_into_document(self, new_books_latex: str) -> bool:
        """Insert new books into the YouTube Channels section"""
        # Pattern to find the YouTube Channels section
        pattern = r'(\\subsection\{Books from YouTube Channels\}[^{]*\\begin\{itemize\})(.*?)(\\end\{itemize\})'
        
        match = re.search(pattern, self.existing_content, re.DOTALL)
        
        if match:
            # Replace the content inside itemize
            replacement = f"{match.group(1)}\n{new_books_latex}\n{match.group(3)}"
            self.existing_content = re.sub(pattern, replacement, self.existing_content, flags=re.DOTALL)
        else:
            print("⚠️ YouTube Channels section not found, creating new section...")
            self._create_youtube_section(new_books_latex)
        
        # Write updated content
        try:
            with open(self.tex_file, 'w', encoding='utf-8') as f:
                f.write(self.existing_content)
            return True
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False
    
    def _create_youtube_section(self, new_books_latex: str):
        """Create YouTube Channels section if it doesn't exist"""
        new_section = f"""
%=============================================================================
\\subsection{{Books from YouTube Channels}}

\\begin{{itemize}}
{new_books_latex}
\\end{{itemize}}
"""
        
        # Insert before appendices or at the end
        appendix_pattern = r'(\\appendix)'
        if re.search(appendix_pattern, self.existing_content):
            self.existing_content = re.sub(appendix_pattern, new_section + r'\1', self.existing_content)
        else:
            # Insert before the end of document
            self.existing_content = self.existing_content.replace(
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
    
    def _create_selection_report(self, selected_books: List[Dict], books_by_channel: Dict):
        """Create a detailed report of selected books"""
        with open('youtube_books_report.txt', 'w', encoding='utf-8') as f:
            f.write("YOUTUBE CHANNELS BOOKS - SELECTION REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Summary by channel
            f.write("SUMMARY BY CHANNEL:\n")
            f.write("-"*40 + "\n")
            for channel, books in books_by_channel.items():
                status_count = {'f': 0, 'p': 0, 't': 0}
                for book in books:
                    status_count[book.get('status', 't')] += 1
                
                f.write(f"{channel}:\n")
                f.write(f"  Total: {len(books)} books\n")
                f.write(f"  Finished: {status_count['f']}, In Progress: {status_count['p']}, To Read: {status_count['t']}\n\n")
            
            # Detailed list
            f.write("\nDETAILED BOOK LIST:\n")
            f.write("-"*40 + "\n")
            
            for book in selected_books:
                status_map = {'f': 'FINISHED', 'p': 'IN PROGRESS', 't': 'TO READ'}
                status = status_map.get(book.get('status', 't'), 'TO READ')
                f.write(f"✓ {status}: {book['title']}\n")
                f.write(f"  Author: {book['author']}\n")
                f.write(f"  Channel: {book['channel']}\n")
                f.write(f"  Source: {book.get('source', 'manual')}\n\n")
        
        print("✓ Detailed report: youtube_books_report.txt")


def main():
    print("\n" + "="*80)
    print("YOUTUBE CHANNEL BOOK EXTRACTOR AND MERGER")
    print("="*80 + "\n")
    
    # Initialize extractor
    extractor = YouTubeBookExtractor("_merged.tex", "subscriptions.csv")
    
    # Load existing document
    if not extractor.load_document():
        return
    
    # Load subscriptions
    if not extractor.load_subscriptions():
        return
    
    # Select channels to process
    selected_channels = extractor.interactive_channel_selection()
    if not selected_channels:
        print("❌ No channels selected.")
        return
    
    print(f"\n✅ Selected {len(selected_channels)} channels for processing")
    
    # Discover and extract books
    all_books = extractor.interactive_book_discovery(selected_channels)
    
    if not all_books:
        print("❌ No books discovered or entered.")
        return
    
    print(f"\n📚 Total books discovered: {len(all_books)}")
    
    # Final selection
    selected_books = extractor.interactive_selection(all_books)
    
    if selected_books:
        # Merge books
        extractor.merge_books(selected_books)
        
        print(f"\n{'='*80}")
        print("PROCESS COMPLETE!")
        print(f"{'='*80}")
        print(f"📚 Books added: {len(selected_books)}")
        print(f"📺 Channels: {len(set(b['channel'] for b in selected_books))}")
        print(f"📄 LaTeX file updated: _merged.tex")
        print(f"📊 Report created: youtube_books_report.txt")
        print(f"\nThe books have been added to the 'Books from YouTube Channels' section.")
        print(f"{'='*80}\n")
    else:
        print("\n❌ No books were selected.")


if __name__ == "__main__":
    main()