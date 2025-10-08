"""
Generalized YouTube Channel Book Merger
Adds books from multiple YouTube channels to LaTeX file with proper formatting
"""

import re
import json
import csv
from typing import List, Dict, Set, Optional
import os

class YouTubeBookMerger:
    def __init__(self, tex_file: str = "_merged.tex", subscriptions_file: str = "subscriptions.csv"):
        self.tex_file = tex_file
        self.subscriptions_file = subscriptions_file
        self.existing_content = ""
        self.existing_books = set()
        self.channel_data = {}
        
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
                    self.channel_data[channel_id] = {
                        'title': row['Channel Title'],
                        'url': row['Channel Url']
                    }
            print(f"✓ Loaded {len(self.channel_data)} channels from subscriptions")
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
    
    def discover_book_files(self) -> Dict[str, str]:
        """Discover all book JSON files in the directory"""
        book_files = {}
        
        # Look for pattern: {channel_id}_books_final.json
        for filename in os.listdir('.'):
            if filename.endswith('_books_final.json'):
                # Extract channel ID from filename
                channel_id = filename.replace('_books_final.json', '')
                book_files[channel_id] = filename
                print(f"✓ Found book file: {filename} for channel ID: {channel_id}")
        
        # Also look for generic book files
        for filename in os.listdir('.'):
            if filename.endswith('.json') and 'book' in filename.lower():
                if filename not in book_files.values():
                    # Try to extract channel info from content
                    channel_id = self._extract_channel_from_json(filename)
                    if channel_id:
                        book_files[channel_id] = filename
                    else:
                        book_files[f"generic_{len(book_files)}"] = filename
        
        return book_files
    
    def _extract_channel_from_json(self, filename: str) -> Optional[str]:
        """Try to extract channel ID from JSON content"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Look for channel information in JSON
            if 'channel_id' in data:
                return data['channel_id']
            elif 'channel_name' in data:
                # Try to match with subscriptions
                channel_name = data['channel_name'].lower()
                for channel_id, info in self.channel_data.items():
                    if info['title'].lower() in channel_name or channel_name in info['title'].lower():
                        return channel_id
        except:
            pass
        return None
    
    def load_books_from_file(self, filename: str, channel_info: Dict) -> List[Dict]:
        """Load and filter books from a JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                books = data
            elif 'books' in data:
                books = data['books']
            elif 'recommendations' in data:
                books = data['recommendations']
            else:
                print(f"⚠️ Unknown JSON structure in {filename}")
                books = []
            
            print(f"✓ Loaded {len(books)} books from {filename}")
            return self._filter_real_books(books, channel_info)
        except FileNotFoundError:
            print(f"❌ Error: {filename} not found")
            return []
        except json.JSONDecodeError:
            print(f"❌ Error: {filename} contains invalid JSON")
            return []
    
    def _filter_real_books(self, books: List[Dict], channel_info: Dict) -> List[Dict]:
        """Filter out non-book entries"""
        real_books = []
        channel_name = channel_info.get('title', 'Unknown Channel')
        
        for book in books:
            # Handle different book structures
            if isinstance(book, str):
                book = {'title': book, 'author': 'Unknown'}
            
            title = self._clean_title(book.get('title', ''))
            if not title:
                continue
                
            if self._is_real_book(title):
                clean_book = {
                    'title': title,
                    'author': book.get('author', 'Unknown'),
                    'channel': channel_name,
                    'channel_url': channel_info.get('url', ''),
                    'source_file': channel_info.get('source_file', '')
                }
                
                # Add additional fields if present
                if 'video_title' in book:
                    clean_book['video_title'] = book['video_title']
                if 'year' in book:
                    clean_book['year'] = book['year']
                
                real_books.append(clean_book)
        
        # Sort alphabetically
        real_books.sort(key=lambda x: x['title'].lower())
        print(f"✓ Filtered to {len(real_books)} real books from {channel_name}")
        return real_books
    
    def _clean_title(self, title: str) -> str:
        """Clean up book title"""
        if not title:
            return ""
            
        title = title.strip()
        
        # Remove common prefixes and suffixes
        prefixes = ['Book Links\n', 'Books\n', 'Articles\n', 'Recommendations:\n']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        # Clean up trailing colons and other artifacts
        if title.endswith(':'):
            title = title[:-1].strip()
        
        return title
    
    def _is_real_book(self, title: str) -> bool:
        """Determine if entry is a real book"""
        title_lower = title.lower()
        
        # Reject obvious non-books
        reject_indicators = [
            'randomized controlled trial', 'meta-analysis', 'clinical trial', 
            'pilot study', 'eight sleep', 'clearlyfiltered', 'pitcher', 'lamp',
            'shampoo', 'biotin', 'therapy services', 'workout splits',
            'facebook', 'instagram', 'twitter', 'academic profile', 'lab website',
            'newsletter', 'personal website', 'publications:', 'stanford academic',
            'book links', 'articles', 'books\n', 'resources', 'profile:',
            'website:', 'social media:', 'click here', 'learn more', 'visit'
        ]
        
        if any(indicator in title_lower for indicator in reject_indicators):
            return False
        
        # Must have reasonable length and structure
        if len(title) < 5 or len(title) > 200:
            return False
            
        # Reject titles that are just URLs or email addresses
        if re.match(r'^(https?://|www\.|[\w\.-]+@[\w\.-]+)', title_lower):
            return False
        
        return True
    
    def interactive_selection(self, all_books: List[Dict]) -> List[Dict]:
        """Interactive book selection across all channels"""
        print(f"\n{'='*80}")
        print("INTERACTIVE BOOK SELECTION - ALL CHANNELS")
        print(f"{'='*80}")
        
        selected_books = []
        duplicate_count = 0
        skip_remaining = False
        
        for i, book in enumerate(all_books, 1):
            if skip_remaining:
                break
                
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
            
            while True:
                response = input("\nAdd this book? (y)es/(n)o/(s)kip remaining/(a)dd all/(q)uit: ").lower().strip()
                
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
                    skip_remaining = True
                    break
                elif response in ['a', 'add all']:
                    print("✅ ADDING ALL REMAINING")
                    # Add remaining books
                    for remaining in all_books[i-1:]:
                        if remaining['title'].lower() not in self.existing_books:
                            remaining['status'] = 't'
                            selected_books.append(remaining)
                    skip_remaining = True
                    break
                elif response in ['q', 'quit']:
                    print("👋 EXITING SELECTION")
                    return selected_books
                else:
                    print("Please enter: y/yes, n/no, s/skip, a/add all, or q/quit")
        
        print(f"\n{'='*80}")
        print(f"SELECTION COMPLETE")
        print(f"{'='*80}")
        print(f"Books processed: {len(all_books)}")
        print(f"Duplicates skipped: {duplicate_count}")
        print(f"New books selected: {len(selected_books)}")
        
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
        
        # Generate LaTeX for each channel
        all_latex_entries = []
        for channel, books in books_by_channel.items():
            channel_latex = self._generate_channel_section(channel, books)
            all_latex_entries.append(channel_latex)
        
        # Combine all entries
        new_books_latex = '\n\n'.join(all_latex_entries)
        
        # Insert into document
        success = self._insert_into_document(new_books_latex)
        
        if success:
            print(f"✓ Successfully merged {len(selected_books)} books from {len(books_by_channel)} channels into {self.tex_file}")
            self._create_selection_report(selected_books, books_by_channel)
        else:
            print("❌ Failed to merge books into document")
    
    def _generate_channel_section(self, channel: str, books: List[Dict]) -> str:
        """Generate LaTeX section for a specific channel"""
        latex_entries = []
        
        for book in books:
            title = self._escape_latex(book['title'])
            author = self._escape_latex(self._clean_author(book['author']))
            status = book.get('status', 't')
            year = book.get('year', self._extract_year(book))
            
            latex_entries.append(f"\\bookentry[{status}]{{{title}}}{{{author}}}{{{year}}}{{Recommended by {channel}}}")
        
        channel_section = f"% Books from {channel}\n" + "\n".join(latex_entries)
        return channel_section
    
    def _clean_author(self, author: str) -> str:
        """Clean up author field"""
        if author == "Unknown" or not author:
            return "Unknown"
        
        # Remove common artifacts
        clean_author = author
        artifacts = [
            "I interview Dr. ", "my guest is Dr. ", "a light and magnetic field resonance",
            "reducing coding precision during food sca", "est this episode is Dr. ",
            "l series on sleep with Dr. ", "Huberman Lab guests ", "Guest: ",
            "Interview with ", "Discussion with "
        ]
        
        for artifact in artifacts:
            clean_author = clean_author.replace(artifact, "")
        
        return clean_author.strip() or "Unknown"
    
    def _extract_year(self, book: Dict) -> str:
        """Extract year from video title if possible"""
        video_title = book.get('video_title', '')
        year_match = re.search(r'(20\d{2})', video_title)
        return year_match.group(1) if year_match else ""
    
    def _insert_into_document(self, new_books_latex: str) -> bool:
        """Insert new books into the appropriate section"""
        # Pattern to find the YouTube channels subsection with itemize
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
        """Create a report of selected books"""
        with open('youtube_books_selection_report.txt', 'w', encoding='utf-8') as f:
            f.write("YOUTUBE CHANNELS BOOKS - SELECTION REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Summary by channel
            f.write("SUMMARY BY CHANNEL:\n")
            f.write("-"*40 + "\n")
            for channel, books in books_by_channel.items():
                f.write(f"{channel}: {len(books)} books\n")
            f.write("\n")
            
            # Detailed list
            f.write("SELECTED BOOKS:\n")
            f.write("-"*40 + "\n")
            
            for book in selected_books:
                status_map = {'f': 'FINISHED', 'p': 'IN PROGRESS', 't': 'TO READ'}
                status = status_map.get(book.get('status', 't'), 'TO READ')
                f.write(f"✓ {status}: {book['title']}\n")
                f.write(f"  Author: {book['author']}\n")
                f.write(f"  Channel: {book['channel']}\n\n")
        
        print("✓ Selection report: youtube_books_selection_report.txt")


def main():
    print("\n" + "="*80)
    print("YOUTUBE CHANNELS BOOK MERGER")
    print("="*80 + "\n")
    
    # Initialize merger
    merger = YouTubeBookMerger("_merged.tex", "subscriptions.csv")
    
    # Load existing document
    if not merger.load_document():
        return
    
    # Load subscriptions
    if not merger.load_subscriptions():
        return
    
    # Discover book files
    book_files = merger.discover_book_files()
    if not book_files:
        print("❌ No book JSON files found.")
        print("Looking for files ending with '_books_final.json' or containing 'book' in filename")
        return
    
    # Load books from all files
    all_books = []
    for channel_id, filename in book_files.items():
        channel_info = merger.channel_data.get(channel_id, {
            'title': channel_id,
            'url': '',
            'source_file': filename
        })
        books = merger.load_books_from_file(filename, channel_info)
        all_books.extend(books)
    
    if not all_books:
        print("❌ No books found in any JSON files.")
        return
    
    print(f"\n📚 Total books available: {len(all_books)}")
    
    # Interactive selection
    selected_books = merger.interactive_selection(all_books)
    
    if selected_books:
        # Merge books
        merger.merge_books(selected_books)
        
        print(f"\n{'='*80}")
        print("PROCESS COMPLETE!")
        print(f"{'='*80}")
        print(f"📚 Books added: {len(selected_books)}")
        print(f"📺 Channels: {len(set(b['channel'] for b in selected_books))}")
        print(f"📄 LaTeX file updated: _merged.tex")
        print(f"📊 Report created: youtube_books_selection_report.txt")
        print(f"\nThe books have been added to the 'Books from YouTube Channels' section.")
        print(f"{'='*80}\n")
    else:
        print("\n❌ No books were selected.")


if __name__ == "__main__":
    main()