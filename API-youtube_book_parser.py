"""
YouTube Book Discovery - Complete API Version
Analyzes ALL videos from ALL channels using YouTube Data API v3
"""

import re
import csv
from typing import List, Dict, Set
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

class YouTubeBookDiscoveryAPI:
    def __init__(self, tex_file: str = "_merged.tex", subscriptions_file: str = "subscriptions.csv"):
        self.tex_file = tex_file
        self.subscriptions_file = subscriptions_file
        self.existing_content = ""
        self.existing_books = set()
        self.channels = {}
        self.youtube = None
        
        # Book detection patterns
        self.book_patterns = [
            # Quoted titles with context
            r'(?:book|reading|recommend|wrote|published|author)(?:s|ed|ing)?[:\s]+["\']([^"\']{10,150})["\']',
            # Title by Author format
            r'["\']([^"\']{10,150})["\'](?:\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}))',
            # My book / new book patterns
            r'(?:my|our|new|latest|recent)\s+book[:\s]+["\']?([A-Za-z][^"\',.]{10,150})["\']?',
            # Book: Title format
            r'book[:\s]+([A-Z][A-Za-z\s:]{10,150})(?:\s+by|\s*$|\s*[,.\n])',
            # Common reading patterns
            r'(?:reading|finished|started)[:\s]+["\']([^"\']{10,150})["\']',
        ]
    
    def setup_youtube_api(self, api_key: str):
        """Initialize YouTube API client"""
        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            # Test the API key with a simple request
            self.youtube.search().list(part="snippet", maxResults=1, q="test").execute()
            print("✓ YouTube API initialized and validated")
            return True
        except HttpError as e:
            if 'API key' in str(e):
                print(f"✗ API Key Error: {e}")
                print("\n📝 TO GET A NEW API KEY:")
                print("1. Go to: https://console.cloud.google.com/")
                print("2. Create a new project (or select existing)")
                print("3. Enable 'YouTube Data API v3':")
                print("   - Go to 'APIs & Services' > 'Library'")
                print("   - Search 'YouTube Data API v3'")
                print("   - Click 'Enable'")
                print("4. Create credentials:")
                print("   - Go to 'APIs & Services' > 'Credentials'")
                print("   - Click 'Create Credentials' > 'API Key'")
                print("   - Copy your new API key")
            else:
                print(f"✗ API Error: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False
    
    def load_document(self):
        """Load the LaTeX document and parse existing books"""
        try:
            with open(self.tex_file, 'r', encoding='utf-8') as f:
                self.existing_content = f.read()
            
            self.existing_books = self._parse_existing_books()
            print(f"✓ Loaded {len(self.existing_books)} existing books from {self.tex_file}")
            return True
        except FileNotFoundError:
            print(f"✗ Error: {self.tex_file} not found.")
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
            print(f"✗ Error: {self.subscriptions_file} not found")
            return False
    
    def _parse_existing_books(self) -> Set[str]:
        """Extract book titles from LaTeX document"""
        books = set()
        pattern = r'\\bookentry(?:\[[^\]]*\])?\{([^}]+)\}'
        matches = re.findall(pattern, self.existing_content)
        for title in matches:
            books.add(title.strip().lower())
        return books
    
    def get_all_channel_videos(self, channel_id: str) -> List[Dict]:
        """Get ALL videos from a channel using pagination"""
        videos = []
        next_page_token = None
        
        try:
            while True:
                # Request videos from the channel
                request = self.youtube.search().list(
                    part="snippet",
                    channelId=channel_id,
                    maxResults=50,  # Max allowed per request
                    order="date",
                    type="video",
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                # Extract video data
                for item in response.get('items', []):
                    videos.append({
                        'video_id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description']
                    })
                
                # Check for more pages
                next_page_token = response.get('nextPageToken')
                
                if not next_page_token:
                    break
                
                # Small delay to respect rate limits
                time.sleep(0.1)
            
            return videos
            
        except HttpError as e:
            print(f"    ⚠️ API Error: {str(e)[:80]}")
            return videos  # Return what we got so far
    
    def extract_books_from_text(self, text: str) -> List[Dict]:
        """Extract book mentions from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        
        # Quick check for book-related keywords
        if not any(keyword in text_lower for keyword in ['book', 'author', 'reading', 'wrote', 'published']):
            return []
        
        books = []
        
        # Try each pattern
        for pattern in self.book_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                if isinstance(match, tuple):
                    title = match[0].strip()
                    author = match[1].strip() if len(match) > 1 and match[1] else "Unknown"
                else:
                    title = match.strip()
                    author = "Unknown"
                
                # Validate
                if self._is_valid_book_title(title):
                    books.append({
                        'title': title,
                        'author': author
                    })
        
        return books
    
    def _is_valid_book_title(self, title: str) -> bool:
        """Validate if string looks like a book title"""
        if not (10 <= len(title) <= 150):
            return False
        
        # Skip URLs and common video phrases
        skip_terms = [
            'http', 'www', 'youtube', 'subscribe', 'like and subscribe',
            'watch', 'video', 'channel', 'click here', 'link in description',
            'comment below', 'patreon', 'merch', 'podcast', 'episode'
        ]
        
        title_lower = title.lower()
        if any(term in title_lower for term in skip_terms):
            return False
        
        # Reasonable word count
        words = title.split()
        if len(words) < 2 or len(words) > 20:
            return False
        
        return True
    
    def analyze_channel(self, channel_id: str, channel_info: Dict) -> List[Dict]:
        """Analyze ALL videos from a channel for book mentions"""
        print(f"\n  Analyzing: {channel_info['title']}")
        
        # Get ALL videos
        videos = self.get_all_channel_videos(channel_id)
        
        if not videos:
            print(f"    No videos found")
            return []
        
        print(f"    Retrieved {len(videos)} videos")
        
        # Extract books from all videos
        book_mentions = {}
        
        for video in videos:
            text = f"{video['title']} {video['description']}"
            books = self.extract_books_from_text(text)
            
            for book in books:
                title_key = book['title'].lower()
                
                if title_key not in book_mentions:
                    book_mentions[title_key] = {
                        'title': book['title'],
                        'author': book['author'],
                        'count': 1,
                        'sample_videos': [video['title'][:80]]
                    }
                else:
                    book_mentions[title_key]['count'] += 1
                    if len(book_mentions[title_key]['sample_videos']) < 3:
                        book_mentions[title_key]['sample_videos'].append(video['title'][:80])
        
        # Convert to list and sort by mentions
        all_books = []
        for book_data in book_mentions.values():
            all_books.append({
                'title': book_data['title'],
                'author': book_data['author'],
                'mentions': book_data['count'],
                'sample_videos': book_data['sample_videos'],
                'channel': channel_info['title'],
                'channel_url': channel_info['url']
            })
        
        all_books.sort(key=lambda x: x['mentions'], reverse=True)
        
        if all_books:
            print(f"    📚 Found {len(all_books)} book(s) - {sum(b['mentions'] for b in all_books)} total mentions")
        else:
            print(f"    No books detected")
        
        return all_books
    
    def scan_all_channels(self):
        """Scan ALL channels for book recommendations"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE CHANNEL SCAN - ALL VIDEOS VIA API")
        print(f"{'='*80}")
        print(f"Analyzing {len(self.channels)} channels...")
        print("Using YouTube Data API to fetch complete video data")
        print(f"{'='*80}")
        
        all_channel_books = []
        channels_with_books = 0
        total_books = 0
        total_videos = 0
        
        for i, (channel_id, channel_info) in enumerate(self.channels.items(), 1):
            print(f"\n[{i}/{len(self.channels)}]", end="")
            
            books = self.analyze_channel(channel_id, channel_info)
            
            if books:
                channels_with_books += 1
                total_books += len(books)
                all_channel_books.append({
                    'channel': channel_info['title'],
                    'channel_url': channel_info['url'],
                    'books': books
                })
            
            # Rate limiting for API quota management
            time.sleep(0.5)
            
            # Progress update
            if i % 20 == 0:
                print(f"\n  📊 Progress: {i}/{len(self.channels)} | {channels_with_books} channels with books | {total_books} unique books")
        
        print(f"\n{'='*80}")
        print(f"SCAN COMPLETE")
        print(f"{'='*80}")
        print(f"📺 Channels analyzed: {len(self.channels)}")
        print(f"📚 Channels with books: {channels_with_books}")
        print(f"📖 Total unique books: {total_books}")
        
        return all_channel_books
    
    def interactive_selection(self, channel_books: List[Dict]) -> List[Dict]:
        """Interactive selection of books"""
        if not channel_books:
            print("\n❌ No books discovered")
            return []
        
        print(f"\n{'='*80}")
        print("DISCOVERED BOOKS - REVIEW AND SELECT")
        print(f"{'='*80}")
        
        selected_books = []
        
        for channel_data in channel_books:
            print(f"\n{'='*60}")
            print(f"Channel: {channel_data['channel']}")
            print(f"Books found: {len(channel_data['books'])}")
            print(f"{'='*60}")
            
            for i, book in enumerate(channel_data['books'], 1):
                print(f"\n  [{i}] {book['title']}")
                if book['author'] != "Unknown":
                    print(f"      Author: {book['author']}")
                print(f"      Mentioned {book['mentions']}x across videos")
                print(f"      Sample: {book['sample_videos'][0][:70]}...")
            
            choice = input(f"\nAdd books from {channel_data['channel']}? (a)ll/(s)elect/(n)one/(q)uit: ").lower().strip()
            
            if choice == 'q':
                print("  Exiting selection...")
                break
            elif choice == 'a':
                for book in channel_data['books']:
                    if book['title'].lower() not in self.existing_books:
                        selected_books.append(book)
                print(f"  ✅ Added all {len(channel_data['books'])} books")
            elif choice == 's':
                nums = input("  Enter book numbers (e.g., 1,3,5): ").strip()
                try:
                    for num in [int(x.strip()) for x in nums.split(',')]:
                        if 1 <= num <= len(channel_data['books']):
                            book = channel_data['books'][num-1]
                            if book['title'].lower() not in self.existing_books:
                                selected_books.append(book)
                    print(f"  ✅ Added selected books")
                except ValueError:
                    print("  ✗ Invalid input")
            else:
                print(f"  ⏩ Skipped")
        
        return selected_books
    
    def merge_books(self, selected_books: List[Dict]):
        """Merge selected books into LaTeX document"""
        if not selected_books:
            print("❌ No books selected for merging.")
            return
        
        print("\n" + "="*80)
        print("SET READING STATUS FOR EACH BOOK")
        print("="*80)
        
        for book in selected_books:
            print(f"\n{book['title']}")
            if book['author'] != "Unknown":
                print(f"  by {book['author']}")
            print(f"  from {book['channel']} ({book['mentions']} mentions)")
            status = input("  Status? (f)inished/(p)rogress/(t)o read [t]: ").lower().strip()
            book['status'] = status if status in ['f', 'p'] else 't'
        
        new_books_latex = self._generate_latex_entries(selected_books)
        success = self._insert_into_document(new_books_latex)
        
        if success:
            print(f"\n✓ Successfully merged {len(selected_books)} books into {self.tex_file}")
    
    def _generate_latex_entries(self, books: List[Dict]) -> str:
        """Generate LaTeX entries for books"""
        latex_entries = []
        
        for book in books:
            title = self._escape_latex(book['title'])
            author = self._escape_latex(book.get('author', 'Unknown'))
            status = book.get('status', 't')
            channel = book.get('channel', 'YouTube')
            mentions = book.get('mentions', 1)
            
            note = f"Mentioned {mentions}x on {channel}"
            latex_entries.append(
                f"\\bookentry[{status}]{{{title}}}{{{author}}}{{}}{{YouTube: {note}}}"
            )
        
        return "\n".join(latex_entries)
    
    def _insert_into_document(self, new_books_latex: str) -> bool:
        """Insert new books into LaTeX document"""
        pattern = r'(\\subsection\{Books from YouTube Channels\}[^{]*\\begin\{itemize\})(.*?)(\\end\{itemize\})'
        match = re.search(pattern, self.existing_content, re.DOTALL)
        
        if match:
            existing_books = match.group(2)
            replacement = f"{match.group(1)}{existing_books}\n{new_books_latex}\n{match.group(3)}"
            self.existing_content = re.sub(pattern, replacement, self.existing_content, flags=re.DOTALL)
        else:
            self._create_youtube_section(new_books_latex)
        
        try:
            with open(self.tex_file, 'w', encoding='utf-8') as f:
                f.write(self.existing_content)
            return True
        except Exception as e:
            print(f"✗ Error writing file: {e}")
            return False
    
    def _create_youtube_section(self, new_books_latex: str):
        """Create YouTube Channels section if it doesn't exist"""
        new_section = f"""
\\subsection{{Books from YouTube Channels}}

\\begin{{itemize}}
{new_books_latex}
\\end{{itemize}}
"""
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


def main():
    print("\n" + "="*80)
    print("YOUTUBE BOOK DISCOVERY - COMPLETE API VERSION")
    print("="*80)
    print("Analyzes ALL videos from ALL channels using YouTube Data API v3")
    print("="*80 + "\n")
    
    # Get API key
    api_key = input("Enter your YouTube API key: ").strip()
    
    if not api_key:
        print("\n❌ API key required!")
        print("\n📝 TO GET AN API KEY:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable 'YouTube Data API v3'")
        print("4. Create credentials (API Key)")
        print("5. Copy the key and paste it here")
        return
    
    processor = YouTubeBookDiscoveryAPI("_merged.tex", "subscriptions.csv")
    
    if not processor.setup_youtube_api(api_key):
        return
    
    if not processor.load_document():
        return
    
    if not processor.load_subscriptions():
        return
    
    print("\n✅ Ready to scan all channels comprehensively")
    print("⚠️  Note: YouTube API has quota limits (10,000 units/day)")
    print("   Each channel scan uses ~1-5 units per video")
    proceed = input("\nContinue? (y/n): ").lower().strip()
    
    if proceed != 'y':
        print("Cancelled.")
        return
    
    channel_books = processor.scan_all_channels()
    
    if not channel_books:
        print("\n❌ No books discovered")
        return
    
    selected_books = processor.interactive_selection(channel_books)
    
    if selected_books:
        processor.merge_books(selected_books)
        
        print(f"\n{'='*80}")
        print("COMPLETE!")
        print(f"{'='*80}")
        print(f"📚 Books added: {len(selected_books)}")
        print(f"📄 File updated: _merged.tex")
        print(f"{'='*80}\n")
    else:
        print("\n❌ No books were selected.")


if __name__ == "__main__":
    main()
