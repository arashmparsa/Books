"""
Focused YouTube Book Processor
Only processes channels known to recommend books
"""

import re
import csv
import os
from typing import List, Dict, Set

class FocusedBookProcessor:
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
    
    def get_book_recommending_channels(self):
        """Get channels known to recommend books"""
        # Known book-recommending channels
        book_channels = {
            # Huberman Lab and similar neuroscience/health channels
            'UCkZjTZNvuxq1CYMS3cwZa1Q': 'Andrew Huberman',  # Huberman Lab
            'UCiS882YPwsZ9kRSMOe2xHUg': 'FoundMyFitness',   # Rhonda Patrick
            'UC8butISFwT-Wl7EV0hUK0BQ': 'freeCodeCamp.org', # Programming books
            'UCYO_jab_esuFRV4b17AJtAw': '3Blue1Brown',      # Math books
            'UCs4aHmggTfFrpkPcWSaBN9g': 'Pursuit of Wonder', # Philosophy books
            'UCZYTClx2T1of7BRZ86-8fow': 'SciShow',          # Science books
            'UC6nSFpj9HTCZ5t-N3Rm3-HA': 'Vsauce',           # Science/psych books
        }
        
        # Also look for channels with keywords indicating book recommendations
        book_keywords = [
            'book', 'books', 'reading', 'literature', 'author', 'writer',
            'library', 'review', 'recommend', 'suggest', 'reading list'
        ]
        
        found_channels = []
        
        # Check for known channels in subscriptions
        for channel_id, channel_name in book_channels.items():
            if channel_id in self.channels:
                found_channels.append({
                    'id': channel_id,
                    'title': channel_name,
                    'url': self.channels[channel_id]['url'],
                    'reason': 'known_book_channel'
                })
        
        # Check for channels with book-related keywords
        for channel_id, info in self.channels.items():
            channel_lower = info['title'].lower()
            if any(keyword in channel_lower for keyword in book_keywords):
                found_channels.append({
                    'id': channel_id,
                    'title': info['title'],
                    'url': info['url'],
                    'reason': 'book_keyword_in_name'
                })
        
        return found_channels
    
    def get_huberman_lab_books(self):
        """Get common books recommended by Huberman Lab"""
        return [
            {"title": "The Brain That Changes Itself", "author": "Norman Doidge"},
            {"title": "Behave", "author": "Robert Sapolsky"},
            {"title": "The Tell-Tale Brain", "author": "V.S. Ramachandran"},
            {"title": "Principles of Neural Science", "author": "Eric R. Kandel"},
            {"title": "Why We Sleep", "author": "Matthew Walker"},
            {"title": "The Talent Code", "author": "Daniel Coyle"},
            {"title": "Peak", "author": "Anders Ericsson"},
            {"title": "The Power of Habit", "author": "Charles Duhigg"},
            {"title": "Atomic Habits", "author": "James Clear"},
            {"title": "Dopamine Nation", "author": "Anna Lembke"},
            {"title": "The Fourth Turning", "author": "William Strauss & Neil Howe"},
            {"title": "Can't Hurt Me", "author": "David Goggins"},
            {"title": "The Body Keeps the Score", "author": "Bessel van der Kolk"},
            {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman"},
            {"title": "The Man Who Mistook His Wife for a Hat", "author": "Oliver Sacks"}
        ]
    
    def get_channel_specific_books(self, channel_name: str):
        """Get books specific to certain channels"""
        channel_lower = channel_name.lower()
        
        if any(keyword in channel_lower for keyword in ['huberman', 'neuroscience', 'brain']):
            return self.get_huberman_lab_books()
        
        elif any(keyword in channel_lower for keyword in ['math', 'mathematics']):
            return [
                {"title": "Principles of Mathematical Analysis", "author": "Walter Rudin"},
                {"title": "Linear Algebra Done Right", "author": "Sheldon Axler"},
                {"title": "Introduction to Linear Algebra", "author": "Gilbert Strang"},
                {"title": "How to Solve It", "author": "George Pólya"},
                {"title": "Gödel, Escher, Bach", "author": "Douglas Hofstadter"}
            ]
        
        elif any(keyword in channel_lower for keyword in ['programming', 'coding', 'code']):
            return [
                {"title": "Clean Code", "author": "Robert C. Martin"},
                {"title": "The Pragmatic Programmer", "author": "Andrew Hunt, David Thomas"},
                {"title": "Design Patterns", "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides"},
                {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein"},
                {"title": "Structure and Interpretation of Computer Programs", "author": "Harold Abelson, Gerald Jay Sussman"}
            ]
        
        elif any(keyword in channel_lower for keyword in ['science', 'physics']):
            return [
                {"title": "A Brief History of Time", "author": "Stephen Hawking"},
                {"title": "The Selfish Gene", "author": "Richard Dawkins"},
                {"title": "Cosmos", "author": "Carl Sagan"},
                {"title": "The Double Helix", "author": "James D. Watson"},
                {"title": "The Elegant Universe", "author": "Brian Greene"}
            ]
        
        return []
    
    def process_book_recommending_channels(self):
        """Process only channels that recommend books"""
        print(f"\n{'='*80}")
        print("PROCESSING BOOK-RECOMMENDING CHANNELS")
        print(f"{'='*80}")
        
        book_channels = self.get_book_recommending_channels()
        
        if not book_channels:
            print("❌ No known book-recommending channels found in subscriptions.")
            print("Looking for channels like Huberman Lab, FoundMyFitness, etc.")
            return []
        
        print(f"\nFound {len(book_channels)} potential book-recommending channels:")
        for i, channel in enumerate(book_channels, 1):
            print(f"  {i}. {channel['title']} ({channel['reason']})")
        
        all_books = []
        
        for channel in book_channels:
            print(f"\n{'='*60}")
            print(f"PROCESSING: {channel['title']}")
            print(f"{'='*60}")
            
            # Get suggested books for this channel
            suggested_books = self.get_channel_specific_books(channel['title'])
            
            if suggested_books:
                print(f"\n📚 Suggested books for {channel['title']}:")
                for i, book in enumerate(suggested_books, 1):
                    print(f"  {i}. {book['title']} by {book['author']}")
                
                while True:
                    choice = input(f"\nAdd books for {channel['title']}? (a)ll/(s)elect/(n)one/(m)anual: ").lower().strip()
                    
                    if choice == 'a':
                        # Add all suggested books
                        for book in suggested_books:
                            book.update({
                                'channel': channel['title'],
                                'channel_url': channel['url'],
                                'source': 'channel_suggestion'
                            })
                            all_books.append(book)
                        print(f"✅ Added all {len(suggested_books)} suggested books")
                        break
                    
                    elif choice == 's':
                        # Let user select specific books
                        selected_nums = input("Enter book numbers to add (e.g., 1,3,5): ").strip()
                        try:
                            numbers = [int(x.strip()) for x in selected_nums.split(',')]
                            valid_numbers = [n for n in numbers if 1 <= n <= len(suggested_books)]
                            
                            for num in valid_numbers:
                                book = suggested_books[num-1].copy()
                                book.update({
                                    'channel': channel['title'],
                                    'channel_url': channel['url'],
                                    'source': 'channel_suggestion'
                                })
                                all_books.append(book)
                            print(f"✅ Added {len(valid_numbers)} books")
                        except ValueError:
                            print("❌ Invalid input")
                        break
                    
                    elif choice == 'n':
                        print(f"⏩ Skipped {channel['title']}")
                        break
                    
                    elif choice == 'm':
                        # Manual entry
                        manual_books = self._manual_book_entry(channel)
                        all_books.extend(manual_books)
                        break
                    
                    else:
                        print("❌ Please enter: a/all, s/select, n/none, or m/manual")
            else:
                print(f"❌ No book suggestions available for {channel['title']}")
                manual_books = self._manual_book_entry(channel)
                all_books.extend(manual_books)
        
        return all_books
    
    def _manual_book_entry(self, channel: Dict) -> List[Dict]:
        """Manual book entry for a channel"""
        books = []
        print(f"\nManual entry for: {channel['title']}")
        print("Format: 'Title' by 'Author' or just 'Title'")
        print("Enter 'done' when finished")
        print("-" * 40)
        
        while True:
            entry = input("Book: ").strip()
            if entry.lower() in ['done', '']:
                break
            
            # Parse entry
            if ' by ' in entry.lower():
                parts = entry.split(' by ', 1)
                title, author = parts[0].strip(), parts[1].strip()
            else:
                title, author = entry, "Unknown"
            
            if title:
                books.append({
                    'title': title,
                    'author': author,
                    'channel': channel['title'],
                    'channel_url': channel['url'],
                    'source': 'manual_entry'
                })
                print(f"✓ Added: {title}")
        
        return books
    
    def interactive_selection(self, all_books: List[Dict]) -> List[Dict]:
        """Final interactive selection of books"""
        if not all_books:
            return []
        
        print(f"\n{'='*80}")
        print("FINAL BOOK SELECTION")
        print(f"{'='*80}")
        print(f"Review {len(all_books)} books before adding to LaTeX:")
        
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
            
            response = input("Add this book? (y)es/(n)o/(a)dd all remaining: ").lower().strip()
            
            if response in ['y', 'yes']:
                status = self._get_reading_status()
                book['status'] = status
                selected_books.append(book)
                print("✓ ADDED")
            elif response in ['n', 'no']:
                print("✗ SKIPPED")
            elif response in ['a', 'add all']:
                print("✅ ADDING ALL REMAINING")
                for remaining in all_books[i-1:]:
                    if remaining['title'].lower() not in self.existing_books:
                        remaining['status'] = 't'
                        selected_books.append(remaining)
                break
        
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
        with open('book_recommendations_report.txt', 'w', encoding='utf-8') as f:
            f.write("BOOK RECOMMENDATIONS FROM YOUTUBE CHANNELS\n")
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
                f.write(f"  Channel: {book['channel']}\n")
                f.write(f"  Source: {book.get('source', 'unknown')}\n\n")
        
        print("✓ Report created: book_recommendations_report.txt")


def main():
    print("\n" + "="*80)
    print("FOCUSED YOUTUBE BOOK PROCESSOR")
    print("="*80 + "\n")
    print("This script focuses ONLY on channels known to recommend books")
    print("like Huberman Lab, FoundMyFitness, educational channels, etc.")
    print("="*80 + "\n")
    
    # Initialize processor
    processor = FocusedBookProcessor("_merged.tex", "subscriptions.csv")
    
    # Load existing document
    if not processor.load_document():
        return
    
    # Load subscriptions
    if not processor.load_subscriptions():
        return
    
    # Process only book-recommending channels
    all_books = processor.process_book_recommending_channels()
    
    if not all_books:
        print("\n❌ No books were found or entered.")
        return
    
    print(f"\n📚 Total books collected: {len(all_books)}")
    
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
        print(f"📊 Report created: book_recommendations_report.txt")
        print(f"\nThe books have been added to the 'Books from YouTube Channels' section.")
        print(f"{'='*80}\n")
    else:
        print("\n❌ No books were selected.")


if __name__ == "__main__":
    main()