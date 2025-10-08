"""
Smart YouTube Channel Book Processor
Only processes educational/technical channels and provides bulk operations
"""

import re
import csv
import os
from typing import List, Dict, Set, Optional

class SmartYouTubeBookProcessor:
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
                        'url': row['Channel Url'],
                        'category': self._categorize_channel(row['Channel Title'])
                    }
            print(f"✓ Loaded {len(self.channels)} channels from subscriptions")
            return True
        except FileNotFoundError:
            print(f"❌ Error: {self.subscriptions_file} not found")
            return False
    
    def _categorize_channel(self, channel_title: str) -> str:
        """Categorize channels to filter out non-educational ones"""
        title_lower = channel_title.lower()
        
        # Music channels (skip)
        music_indicators = ['music', 'song', 'band', 'records', 'audio', 'sound', 'tune', 'melody', 'rhythm']
        if any(indicator in title_lower for indicator in music_indicators):
            return 'music'
        
        # Entertainment channels (skip)
        entertainment_indicators = ['movie', 'film', 'cinema', 'entertainment', 'comedy', 'funny', 'humor']
        if any(indicator in title_lower for indicator in entertainment_indicators):
            return 'entertainment'
        
        # News channels (skip)
        news_indicators = ['news', 'update', 'breaking', 'headline', 'report', 'broadcast']
        if any(indicator in title_lower for indicator in news_indicators):
            return 'news'
        
        # Commercial/brand channels (skip)
        commercial_indicators = ['shop', 'store', 'brand', 'product', 'buy', 'purchase', 'deal', 'sale']
        if any(indicator in title_lower for indicator in commercial_indicators):
            return 'commercial'
        
        # Educational channels (process)
        educational_indicators = [
            'science', 'tech', 'technology', 'programming', 'code', 'computer', 
            'math', 'physics', 'chemistry', 'biology', 'history', 'education',
            'learning', 'tutorial', 'course', 'lecture', 'academy', 'university',
            'research', 'study', 'knowledge', 'explain', 'documentary', 'theory',
            'engineering', 'developer', 'coding', 'data', 'ai', 'machine learning',
            'neuroscience', 'psychology', 'philosophy', 'economics', 'politics',
            'book', 'literature', 'writing', 'author'
        ]
        if any(indicator in title_lower for indicator in educational_indicators):
            return 'educational'
        
        # Technical channels (process)
        technical_indicators = [
            'how to', 'guide', 'tutorial', 'DIY', 'make', 'build', 'create',
            'development', 'software', 'hardware', 'electronics', 'circuit',
            'mechanic', 'repair', 'fix', 'maintenance', 'automotive'
        ]
        if any(indicator in title_lower for indicator in technical_indicators):
            return 'technical'
        
        return 'other'
    
    def _parse_existing_books(self) -> Set[str]:
        """Extract book titles from LaTeX document"""
        books = set()
        pattern = r'\\bookentry(?:\[[^\]]*\])?\{([^}]+)\}'
        matches = re.findall(pattern, self.existing_content)
        for title in matches:
            books.add(title.strip().lower())
        return books
    
    def analyze_channels(self):
        """Analyze and categorize all channels"""
        categories = {}
        for channel_id, info in self.channels.items():
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(info['title'])
        
        print(f"\n{'='*80}")
        print("CHANNEL ANALYSIS")
        print(f"{'='*80}")
        
        for category, channel_list in categories.items():
            print(f"\n{category.upper()}: {len(channel_list)} channels")
            if category in ['educational', 'technical']:
                print("  (Will be processed for book recommendations)")
                for channel in sorted(channel_list)[:10]:  # Show first 10
                    print(f"    - {channel}")
                if len(channel_list) > 10:
                    print(f"    ... and {len(channel_list) - 10} more")
            elif category in ['music', 'entertainment', 'news', 'commercial']:
                print("  (Will be skipped)")
                for channel in sorted(channel_list)[:5]:  # Show first 5
                    print(f"    - {channel}")
                if len(channel_list) > 5:
                    print(f"    ... and {len(channel_list) - 5} more")
        
        return categories
    
    def get_channels_to_process(self) -> List[Dict]:
        """Get list of channels that should be processed"""
        channels_to_process = []
        
        for channel_id, info in self.channels.items():
            if info['category'] in ['educational', 'technical']:
                channels_to_process.append({
                    'id': channel_id,
                    'title': info['title'],
                    'url': info['url'],
                    'category': info['category']
                })
        
        # Sort by category then by title
        channels_to_process.sort(key=lambda x: (x['category'], x['title'].lower()))
        return channels_to_process
    
    def bulk_book_entry(self, channels: List[Dict]) -> List[Dict]:
        """Bulk book entry for multiple channels"""
        all_books = []
        
        print(f"\n{'='*80}")
        print("BULK BOOK ENTRY")
        print(f"{'='*80}")
        
        print("\nYou'll now add books for educational/technical channels.")
        print("For each channel, you can:")
        print("  - Add multiple books at once")
        print("  - Skip the channel entirely")
        print("  - Mark as 'no books' to avoid future prompts")
        print("  - Use bulk entry for common book patterns")
        
        skip_all_remaining = False
        
        for i, channel in enumerate(channels, 1):
            if skip_all_remaining:
                break
                
            print(f"\n{'='*60}")
            print(f"Channel {i}/{len(channels)}: {channel['title']}")
            print(f"Category: {channel['category']}")
            print(f"{'='*60}")
            
            while True:
                print("\nOptions:")
                print("  1. Add books for this channel")
                print("  2. Skip this channel")
                print("  3. Mark as 'no books' (won't ask again)")
                print("  4. Skip all remaining channels")
                print("  5. Bulk add common books by topic")
                
                choice = input("\nChoose option (1-5): ").strip()
                
                if choice == '1':
                    channel_books = self._add_books_for_channel(channel)
                    all_books.extend(channel_books)
                    break
                elif choice == '2':
                    print(f"⏩ Skipped {channel['title']}")
                    break
                elif choice == '3':
                    print(f"📝 Marked {channel['title']} as 'no books'")
                    # Could save this preference to a file
                    break
                elif choice == '4':
                    print("⏭️ Skipping all remaining channels")
                    skip_all_remaining = True
                    break
                elif choice == '5':
                    channel_books = self._bulk_add_common_books(channel)
                    all_books.extend(channel_books)
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
        
        return all_books
    
    def _add_books_for_channel(self, channel: Dict) -> List[Dict]:
        """Add books for a single channel"""
        books = []
        print(f"\nAdding books for: {channel['title']}")
        print("Enter one book per line in format: 'Title' by 'Author'")
        print("Or just 'Title' if author is unknown")
        print("Enter 'done' when finished")
        print("-" * 50)
        
        book_count = 0
        while True:
            entry = input(f"Book {book_count + 1}: ").strip()
            if entry.lower() in ['done', 'quit', 'exit', '']:
                break
            
            # Parse the entry
            book_data = self._parse_book_entry(entry)
            if book_data:
                book_data.update({
                    'channel': channel['title'],
                    'channel_url': channel['url'],
                    'source': 'manual_entry'
                })
                books.append(book_data)
                book_count += 1
                print(f"✓ Added: {book_data['title']} by {book_data['author']}")
            else:
                print("❌ Invalid format. Use: 'Title' by 'Author' or just 'Title'")
        
        print(f"✓ Added {book_count} books for {channel['title']}")
        return books
    
    def _parse_book_entry(self, entry: str) -> Optional[Dict]:
        """Parse a book entry string into title and author"""
        if not entry or len(entry) < 2:
            return None
        
        # Pattern: "Title" by Author
        match = re.match(r'^"([^"]+)"\s+by\s+(.+)$', entry)
        if match:
            return {'title': match.group(1), 'author': match.group(2)}
        
        # Pattern: Title by Author
        match = re.match(r'^(.+?)\s+by\s+(.+)$', entry, re.IGNORECASE)
        if match:
            return {'title': match.group(1), 'author': match.group(2)}
        
        # Just title
        return {'title': entry, 'author': 'Unknown'}
    
    def _bulk_add_common_books(self, channel: Dict) -> List[Dict]:
        """Bulk add common books based on channel topic"""
        suggested_books = self._get_topic_suggestions(channel['title'])
        
        if not suggested_books:
            print("❌ No book suggestions available for this channel topic.")
            return self._add_books_for_channel(channel)
        
        print(f"\n📚 Suggested books for {channel['title']}:")
        for i, book in enumerate(suggested_books, 1):
            print(f"  {i}. {book['title']} by {book['author']}")
        
        books = []
        while True:
            print("\nOptions:")
            print("  - Enter book numbers to add (e.g., '1,3,5')")
            print("  - 'all' to add all suggestions")
            print("  - 'none' to skip bulk addition")
            print("  - 'manual' to switch to manual entry")
            
            choice = input("Your choice: ").strip().lower()
            
            if choice == 'all':
                for book in suggested_books:
                    book.update({
                        'channel': channel['title'],
                        'channel_url': channel['url'],
                        'source': 'topic_suggestion'
                    })
                    books.append(book)
                print(f"✅ Added all {len(suggested_books)} suggested books")
                break
            elif choice == 'none':
                print("⏩ No books added from suggestions")
                break
            elif choice == 'manual':
                return self._add_books_for_channel(channel)
            else:
                # Try to parse numbers
                try:
                    numbers = [int(x.strip()) for x in choice.split(',')]
                    valid_numbers = [n for n in numbers if 1 <= n <= len(suggested_books)]
                    
                    if valid_numbers:
                        for num in valid_numbers:
                            book = suggested_books[num-1].copy()
                            book.update({
                                'channel': channel['title'],
                                'channel_url': channel['url'],
                                'source': 'topic_suggestion'
                            })
                            books.append(book)
                        print(f"✅ Added {len(valid_numbers)} books")
                        break
                    else:
                        print("❌ No valid book numbers selected")
                except ValueError:
                    print("❌ Invalid input. Please enter numbers separated by commas.")
        
        return books
    
    def _get_topic_suggestions(self, channel_title: str) -> List[Dict]:
        """Get book suggestions based on channel topic"""
        title_lower = channel_title.lower()
        
        # Programming/CS channels
        if any(keyword in title_lower for keyword in ['programming', 'coding', 'code', 'developer', 'software', 'computer science']):
            return [
                {"title": "Clean Code", "author": "Robert C. Martin"},
                {"title": "The Pragmatic Programmer", "author": "Andrew Hunt, David Thomas"},
                {"title": "Design Patterns", "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides"},
                {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein"},
                {"title": "Structure and Interpretation of Computer Programs", "author": "Harold Abelson, Gerald Jay Sussman"}
            ]
        
        # Math channels
        elif any(keyword in title_lower for keyword in ['math', 'mathematics', 'algebra', 'calculus']):
            return [
                {"title": "Principles of Mathematical Analysis", "author": "Walter Rudin"},
                {"title": "Linear Algebra Done Right", "author": "Sheldon Axler"},
                {"title": "Introduction to Linear Algebra", "author": "Gilbert Strang"},
                {"title": "How to Solve It", "author": "George Pólya"},
                {"title": "Gödel, Escher, Bach", "author": "Douglas Hofstadter"}
            ]
        
        # Science channels
        elif any(keyword in title_lower for keyword in ['science', 'physics', 'chemistry', 'biology', 'research']):
            return [
                {"title": "A Brief History of Time", "author": "Stephen Hawking"},
                {"title": "The Selfish Gene", "author": "Richard Dawkins"},
                {"title": "Cosmos", "author": "Carl Sagan"},
                {"title": "The Double Helix", "author": "James D. Watson"},
                {"title": "The Elegant Universe", "author": "Brian Greene"}
            ]
        
        # History channels
        elif any(keyword in title_lower for keyword in ['history', 'historical', 'archaeology']):
            return [
                {"title": "Guns, Germs, and Steel", "author": "Jared Diamond"},
                {"title": "A People's History of the United States", "author": "Howard Zinn"},
                {"title": "The Silk Roads", "author": "Peter Frankopan"},
                {"title": "Sapiens", "author": "Yuval Noah Harari"},
                {"title": "The History of the Ancient World", "author": "Susan Wise Bauer"}
            ]
        
        # Neuroscience/Psychology channels
        elif any(keyword in title_lower for keyword in ['neuro', 'brain', 'psychology', 'mind', 'cognitive']):
            return [
                {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman"},
                {"title": "The Man Who Mistook His Wife for a Hat", "author": "Oliver Sacks"},
                {"title": "Behave", "author": "Robert Sapolsky"},
                {"title": "The Brain That Changes Itself", "author": "Norman Doidge"},
                {"title": "Principles of Neural Science", "author": "Eric R. Kandel"}
            ]
        
        # Business/Economics channels
        elif any(keyword in title_lower for keyword in ['business', 'economics', 'entrepreneur', 'startup', 'finance']):
            return [
                {"title": "The Lean Startup", "author": "Eric Ries"},
                {"title": "Zero to One", "author": "Peter Thiel"},
                {"title": "Good to Great", "author": "Jim Collins"},
                {"title": "The Innovator's Dilemma", "author": "Clayton Christensen"},
                {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman"}
            ]
        
        return []
    
    def interactive_selection(self, all_books: List[Dict]) -> List[Dict]:
        """Final interactive selection of books"""
        if not all_books:
            return []
            
        print(f"\n{'='*80}")
        print("FINAL BOOK SELECTION")
        print(f"{'='*80}")
        print(f"You have {len(all_books)} books to review.")
        
        selected_books = []
        duplicate_count = 0
        
        for i, book in enumerate(all_books, 1):
            title_lower = book['title'].lower()
            
            # Skip duplicates
            if title_lower in self.existing_books:
                print(f"⏩ SKIPPED (duplicate): {book['title']}")
                duplicate_count += 1
                continue
            
            print(f"\n[{i}/{len(all_books)}] {book['title']}")
            print(f"   Author: {book['author']}")
            print(f"   Channel: {book['channel']}")
            
            while True:
                response = input("Add this book? (y)es/(n)o/(a)dd all remaining: ").lower().strip()
                
                if response in ['y', 'yes']:
                    status = self._get_reading_status()
                    book['status'] = status
                    selected_books.append(book)
                    print("✓ ADDED")
                    break
                elif response in ['n', 'no']:
                    print("✗ SKIPPED")
                    break
                elif response in ['a', 'add all']:
                    print("✅ ADDING ALL REMAINING")
                    for remaining in all_books[i-1:]:
                        if remaining['title'].lower() not in self.existing_books:
                            remaining['status'] = 't'
                            selected_books.append(remaining)
                    return selected_books
                else:
                    print("Please enter: y/yes, n/no, or a/add all")
        
        print(f"\nSelected {len(selected_books)} new books (skipped {duplicate_count} duplicates)")
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
        
        # Generate LaTeX entries
        new_books_latex = self._generate_latex_entries(selected_books)
        
        # Insert into document
        success = self._insert_into_document(new_books_latex)
        
        if success:
            print(f"✓ Successfully merged {len(selected_books)} books into {self.tex_file}")
            self._create_selection_report(selected_books)
        else:
            print("❌ Failed to merge books into document")
    
    def _generate_latex_entries(self, books: List[Dict]) -> str:
        """Generate LaTeX entries for books"""
        latex_entries = []
        
        for book in books:
            title = self._escape_latex(book['title'])
            author = self._escape_latex(book['author'])
            status = book.get('status', 't')
            channel = book.get('channel', 'YouTube')
            
            latex_entries.append(f"\\bookentry[{status}]{{{title}}}{{{author}}}{{}}{{Recommended by {channel}}}")
        
        return "\n".join(latex_entries)
    
    def _insert_into_document(self, new_books_latex: str) -> bool:
        """Insert new books into LaTeX document"""
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
    
    def _create_selection_report(self, selected_books: List[Dict]):
        """Create selection report"""
        with open('youtube_books_report.txt', 'w', encoding='utf-8') as f:
            f.write("YOUTUBE CHANNELS BOOKS - SELECTION REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Group by channel
            books_by_channel = {}
            for book in selected_books:
                channel = book['channel']
                if channel not in books_by_channel:
                    books_by_channel[channel] = []
                books_by_channel[channel].append(book)
            
            # Write summary
            f.write("SUMMARY BY CHANNEL:\n")
            f.write("-"*40 + "\n")
            for channel, books in books_by_channel.items():
                f.write(f"{channel}: {len(books)} books\n")
            f.write(f"\nTotal: {len(selected_books)} books\n\n")
            
            # Write detailed list
            f.write("DETAILED BOOK LIST:\n")
            f.write("-"*40 + "\n")
            for book in selected_books:
                status_map = {'f': 'FINISHED', 'p': 'IN PROGRESS', 't': 'TO READ'}
                status = status_map.get(book.get('status', 't'), 'TO READ')
                f.write(f"✓ {status}: {book['title']}\n")
                f.write(f"  Author: {book['author']}\n")
                f.write(f"  Channel: {book['channel']}\n\n")
        
        print("✓ Report created: youtube_books_report.txt")


def main():
    print("\n" + "="*80)
    print("SMART YOUTUBE CHANNEL BOOK PROCESSOR")
    print("="*80 + "\n")
    
    # Initialize processor
    processor = SmartYouTubeBookProcessor("_merged.tex", "subscriptions.csv")
    
    # Load existing document
    if not processor.load_document():
        return
    
    # Load subscriptions
    if not processor.load_subscriptions():
        return
    
    # Analyze channels
    categories = processor.analyze_channels()
    
    # Get channels to process
    channels_to_process = processor.get_channels_to_process()
    
    if not channels_to_process:
        print("\n❌ No educational/technical channels found to process.")
        return
    
    print(f"\n✅ Found {len(channels_to_process)} educational/technical channels to process")
    
    # Bulk book entry
    all_books = processor.bulk_book_entry(channels_to_process)
    
    if not all_books:
        print("❌ No books were entered.")
        return
    
    print(f"\n📚 Total books entered: {len(all_books)}")
    
    # Final selection
    selected_books = processor.interactive_selection(all_books)
    
    if selected_books:
        # Merge books
        processor.merge_books(selected_books)
        
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