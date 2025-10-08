"""
YouTube Book Discovery - Direct Channel Video Analysis
Scrapes actual channel videos and descriptions to find book mentions
"""

import re
import csv
import requests
from typing import List, Dict, Set
import time
import json

class YouTubeBookScraper:
    def __init__(self, tex_file: str = "_merged.tex", subscriptions_file: str = "subscriptions.csv"):
        self.tex_file = tex_file
        self.subscriptions_file = subscriptions_file
        self.existing_content = ""
        self.existing_books = set()
        self.channels = {}
        
        # Book detection patterns - looking for actual book titles
        self.book_patterns = [
            # Quoted titles
            r'(?:book|reading|recommend|wrote|published)(?:s|ed|ing)?[:\s]+["\']([^"\']{10,150})["\']',
            # Title by Author
            r'["\']([^"\']{10,150})["\'](?:\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}))',
            # Common book mention patterns
            r'(?:my book|new book|latest book|book called|book titled)[:\s]+["\']?([A-Za-z][^"\',.]{10,150})["\']?',
            r'(?:reading|finished|started|recommend)[:\s]+["\']([^"\']{10,150})["\']',
            # Book: Title format
            r'book[:\s]+([A-Z][A-Za-z\s:]{10,150})(?:\s+by|\s*$|\s*[,.])',
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
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
    
    def scrape_channel_videos(self, channel_url: str) -> List[Dict]:
        """Scrape ALL videos from a channel page"""
        try:
            # Construct the videos tab URL
            videos_url = channel_url.rstrip('/') + '/videos'
            
            response = requests.get(videos_url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            html = response.text
            
            # Extract video data from the page
            videos = []
            continuation_token = None
            
            # YouTube embeds data in ytInitialData JavaScript object
            data_match = re.search(r'var ytInitialData = ({.*?});', html)
            
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    
                    # Navigate through YouTube's complex JSON structure
                    tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
                    
                    for tab in tabs:
                        tab_renderer = tab.get('tabRenderer', {})
                        if tab_renderer.get('selected'):
                            content = tab_renderer.get('content', {})
                            section_list = content.get('richGridRenderer', {}).get('contents', [])
                            
                            for item in section_list:
                                video_renderer = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})
                                
                                if video_renderer:
                                    title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text', '')
                                    description = video_renderer.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', '')
                                    
                                    if title:
                                        videos.append({
                                            'title': title,
                                            'description': description
                                        })
                                
                                # Check for continuation token to load more videos
                                continuation_renderer = item.get('continuationItemRenderer', {})
                                if continuation_renderer:
                                    continuation_token = continuation_renderer.get('continuationEndpoint', {}).get('continuationCommand', {}).get('token')
                except:
                    pass
            
            # Fallback: regex patterns for ALL video titles and descriptions
            if not videos:
                title_matches = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"', html)
                desc_matches = re.findall(r'"descriptionSnippet":{"runs":\[{"text":"([^"]+)"', html)
                
                for i, title in enumerate(title_matches):
                    description = desc_matches[i] if i < len(desc_matches) else ''
                    videos.append({
                        'title': title,
                        'description': description
                    })
            
            # Try to load more videos using continuation token (if available)
            if continuation_token and len(videos) < 500:  # Reasonable limit to avoid infinite loops
                videos.extend(self._load_more_videos(continuation_token, max_additional=500))
            
            print(f"    Retrieved {len(videos)} videos", end="")
            return videos
            
        except Exception as e:
            print(f"    ⚠️ Scraping error: {str(e)[:50]}")
            return []
    
    def _load_more_videos(self, continuation_token: str, max_additional: int = 500) -> List[Dict]:
        """Load additional videos using continuation token"""
        try:
            # YouTube's browse_ajax endpoint for loading more content
            url = "https://www.youtube.com/youtubei/v1/browse"
            
            # Extract API key from the page if we have it, or use a common one
            api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"  # Common web client key
            
            params = {
                'key': api_key,
                'prettyPrint': 'false'
            }
            
            payload = {
                'continuation': continuation_token,
                'context': {
                    'client': {
                        'clientName': 'WEB',
                        'clientVersion': '2.20231201.01.00'
                    }
                }
            }
            
            response = requests.post(url, params=params, json=payload, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            videos = []
            
            # Parse the continuation response
            continuation_items = data.get('onResponseReceivedActions', [{}])[0].get('appendContinuationItemsAction', {}).get('continuationItems', [])
            
            for item in continuation_items[:max_additional]:
                video_renderer = item.get('richItemRenderer', {}).get('content', {}).get('videoRenderer', {})
                
                if video_renderer:
                    title = video_renderer.get('title', {}).get('runs', [{}])[0].get('text', '')
                    description = video_renderer.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', '')
                    
                    if title:
                        videos.append({
                            'title': title,
                            'description': description
                        })
            
            return videos
            
        except Exception as e:
            return []
    
    def extract_books_from_videos(self, videos: List[Dict]) -> List[Dict]:
        """Extract book mentions from video titles and descriptions"""
        book_mentions = {}
        
        for video in videos:
            text = f"{video['title']} {video['description']}"
            text_lower = text.lower()
            
            # Skip if no book-related keywords
            if not any(keyword in text_lower for keyword in ['book', 'author', 'reading', 'wrote', 'published']):
                continue
            
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
                    
                    # Validate book title
                    if not self._is_valid_book_title(title):
                        continue
                    
                    title_key = title.lower()
                    
                    # Track mentions
                    if title_key not in book_mentions:
                        book_mentions[title_key] = {
                            'title': title,
                            'author': author,
                            'count': 1,
                            'videos': [video['title'][:80]]
                        }
                    else:
                        book_mentions[title_key]['count'] += 1
                        if len(book_mentions[title_key]['videos']) < 3:
                            book_mentions[title_key]['videos'].append(video['title'][:80])
        
        # Convert to list and sort by mention count
        books = []
        for book_data in book_mentions.values():
            books.append({
                'title': book_data['title'],
                'author': book_data['author'],
                'mentions': book_data['count'],
                'sample_videos': book_data['videos']
            })
        
        books.sort(key=lambda x: x['mentions'], reverse=True)
        return books
    
    def _is_valid_book_title(self, title: str) -> bool:
        """Validate if string looks like a book title"""
        # Length check
        if not (10 <= len(title) <= 150):
            return False
        
        # Skip URLs, video-specific terms, etc.
        skip_terms = [
            'http', 'www', 'youtube', 'subscribe', 'like and subscribe',
            'watch', 'video', 'channel', 'click here', 'link in description',
            'comment below', 'share this', 'follow me', 'patreon', 'support'
        ]
        
        title_lower = title.lower()
        if any(term in title_lower for term in skip_terms):
            return False
        
        # Should have reasonable word count
        words = title.split()
        if len(words) < 2 or len(words) > 20:
            return False
        
        return True
    
    def analyze_channel(self, channel_id: str, channel_info: Dict) -> List[Dict]:
        """Analyze a channel's actual videos for book mentions"""
        print(f"\n  Analyzing: {channel_info['title']}")
        
        # Scrape channel videos
        videos = self.scrape_channel_videos(channel_info['url'])
        
        if not videos:
            print(f"    No videos scraped")
            return []
        
        print(f"    Scraped {len(videos)} videos")
        
        # Extract books
        books = self.extract_books_from_videos(videos)
        
        if books:
            print(f"    📚 Found {len(books)} book(s) mentioned")
            # Add channel info
            for book in books:
                book['channel'] = channel_info['title']
                book['channel_url'] = channel_info['url']
        else:
            print(f"    No books detected")
        
        return books
    
    def scan_all_channels(self):
        """Scan all channels for book recommendations"""
        print(f"\n{'='*80}")
        print("SCANNING CHANNELS - ANALYZING ACTUAL VIDEO CONTENT")
        print(f"{'='*80}")
        print(f"Analyzing {len(self.channels)} channels...")
        print("Scraping video titles & descriptions for book mentions")
        print(f"{'='*80}")
        
        all_channel_books = []
        channels_with_books = 0
        total_books = 0
        
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
            
            # Rate limiting
            time.sleep(1.5)
            
            # Progress update
            if i % 20 == 0:
                print(f"\n  📊 Progress: {i}/{len(self.channels)} | {channels_with_books} channels with books | {total_books} books found")
        
        print(f"\n{'='*80}")
        print(f"SCAN COMPLETE")
        print(f"{'='*80}")
        print(f"📺 Channels analyzed: {len(self.channels)}")
        print(f"📚 Channels with books: {channels_with_books}")
        print(f"📖 Total books found: {total_books}")
        
        return all_channel_books
    
    def interactive_selection(self, channel_books: List[Dict]) -> List[Dict]:
        """Interactive selection of books from discovered results"""
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
                print(f"      Mentioned {book['mentions']}x in videos")
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
                    selected = []
                    for num in [int(x.strip()) for x in nums.split(',')]:
                        if 1 <= num <= len(channel_data['books']):
                            book = channel_data['books'][num-1]
                            if book['title'].lower() not in self.existing_books:
                                selected_books.append(book)
                                selected.append(str(num))
                    print(f"  ✅ Added books: {', '.join(selected)}")
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
        
        # Ask for reading status
        print("\n" + "="*80)
        print("SET READING STATUS FOR EACH BOOK")
        print("="*80)
        
        for book in selected_books:
            print(f"\n{book['title']}")
            if book['author'] != "Unknown":
                print(f"  by {book['author']}")
            print(f"  from {book['channel']}")
            status = input("  Status? (f)inished/(p)rogress/(t)o read [t]: ").lower().strip()
            book['status'] = status if status in ['f', 'p'] else 't'
        
        # Generate LaTeX
        new_books_latex = self._generate_latex_entries(selected_books)
        
        # Insert into document
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
    print("YOUTUBE BOOK DISCOVERY - DIRECT VIDEO ANALYSIS")
    print("="*80)
    print("Scrapes actual channel videos to find book mentions")
    print("Works for both recommended books AND books by the creator")
    print("="*80 + "\n")
    
    processor = YouTubeBookScraper("_merged.tex", "subscriptions.csv")
    
    if not processor.load_document():
        return
    
    if not processor.load_subscriptions():
        return
    
    print("\n⚠️  This will take ~8 minutes for 294 channels (1.5s per channel)")
    proceed = input("Continue? (y/n): ").lower().strip()
    
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
