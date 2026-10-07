import os
"""
Complete YouTube Book Extraction Script
Analyzes YouTube channels and extracts book recommendations from video descriptions
"""

import re
import json
import csv
from collections import defaultdict
from typing import List, Dict
import time
from googleapiclient.discovery import build

class YouTubeBookExtractor:
    def __init__(self, api_key: str):
        """Initialize with YouTube Data API key"""
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.books = []
        
    def get_channel_id(self, channel_handle: str) -> str:
        """Convert @username or channel URL to channel ID"""
        if channel_handle.startswith('UC') and len(channel_handle) == 24:
            return channel_handle
            
        username = channel_handle.replace('@', '')
        
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            if response['items']:
                return response['items'][0]['snippet']['channelId']
        except Exception as e:
            print(f"Error finding channel: {e}")
        return None
    
    def get_all_video_ids(self, channel_id: str) -> List[str]:
        """Get all video IDs from a channel"""
        video_ids = []
        
        request = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()
        
        if not response['items']:
            return video_ids
            
        playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        next_page_token = None
        while True:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            video_ids.extend([item['contentDetails']['videoId'] for item in response['items']])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
            time.sleep(0.1)
            
        return video_ids
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get video details including descriptions"""
        videos = []
        
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            request = self.youtube.videos().list(
                part="snippet",
                id=','.join(batch)
            )
            response = request.execute()
            videos.extend(response['items'])
            time.sleep(0.1)
            
        return videos
    
    def extract_books_from_description(self, description: str, video_title: str = "") -> List[Dict]:
        """Extract book information from video description"""
        books = []
        
        # Amazon links
        amazon_pattern = r'(?:https?://)?(?:www\.)?(?:amazon\.com|amzn\.to)/[\w\-/]+'
        amazon_links = re.findall(amazon_pattern, description)
        
        # Book patterns
        book_patterns = [
            r'(?:Book|Read):\s*["\']?([^"\n]+)["\']?\s*(?:by\s+([^"\n]+))?',
            r'["\']([^"]+)["\'](?:\s*by\s+([^"\n]+))?',
            r'(?:Recommended|Featured)\s*Book:\s*([^"\n]+)(?:\s*by\s+([^"\n]+))?',
        ]
        
        for link in amazon_links:
            link_index = description.find(link)
            context_start = max(0, link_index - 100)
            context_end = min(len(description), link_index + len(link) + 100)
            context = description[context_start:context_end]
            
            for pattern in book_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        title = match[0].strip()
                        author = match[1].strip() if len(match) > 1 and match[1] else "Unknown"
                    else:
                        title = match.strip()
                        author = "Unknown"
                    
                    if len(title) > 5 and len(title) < 200:
                        books.append({
                            'title': title,
                            'author': author,
                            'link': link,
                            'video_title': video_title
                        })
        
        # Timestamp sections
        timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*([^\n]+)'
        timestamps = re.findall(timestamp_pattern, description)
        
        for time_str, text in timestamps:
            if any(word in text.lower() for word in ['book', 'read', 'recommend', 'author']):
                clean_text = re.sub(r'https?://\S+', '', text).strip()
                if len(clean_text) > 10:
                    books.append({
                        'title': clean_text,
                        'author': 'Unknown',
                        'link': '',
                        'video_title': video_title,
                        'timestamp': time_str
                    })
        
        return books
    
    def analyze_channel(self, channel_identifier: str) -> Dict:
        """Main method to analyze a channel and extract all books"""
        print(f"Analyzing channel: {channel_identifier}")
        
        channel_id = self.get_channel_id(channel_identifier)
        if not channel_id:
            return {"error": "Channel not found"}
        
        print(f"Channel ID: {channel_id}")
        
        print("Fetching video list...")
        video_ids = self.get_all_video_ids(channel_id)
        print(f"Found {len(video_ids)} videos")
        
        print("Fetching video details...")
        videos = self.get_video_details(video_ids)
        
        print("Extracting books from descriptions...")
        all_books = []
        for video in videos:
            description = video['snippet']['description']
            title = video['snippet']['title']
            books = self.extract_books_from_description(description, title)
            all_books.extend(books)
        
        unique_books = self._deduplicate_books(all_books)
        
        return {
            'channel_id': channel_id,
            'total_videos': len(videos),
            'books_found': len(unique_books),
            'books': unique_books
        }
    
    def _deduplicate_books(self, books: List[Dict]) -> List[Dict]:
        """Remove duplicate books"""
        unique = []
        seen_titles = set()
        
        for book in books:
            title_lower = book['title'].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique.append(book)
        
        return sorted(unique, key=lambda x: x['title'])
    
    def export_to_latex(self, results: Dict, output_file: str = 'books_export.tex'):
        """Export results to LaTeX format"""
        latex_content = [
            r'\documentclass{article}',
            r'\usepackage{hyperref}',
            r'\usepackage{longtable}',
            r'\begin{document}',
            r'\section{Books from YouTube Channel Analysis}',
            '',
            r'\begin{longtable}{|p{6cm}|p{4cm}|p{4cm}|}',
            r'\hline',
            r'\textbf{Book Title} & \textbf{Author} & \textbf{Source Video} \\',
            r'\hline',
        ]
        
        for book in results['books']:
            title = self._escape_latex(book['title'])
            author = self._escape_latex(book['author'])
            video = self._escape_latex(book['video_title'][:50] + '...' if len(book['video_title']) > 50 else book['video_title'])
            
            if book.get('link'):
                title = f"\\href{{{book['link']}}}{{{title}}}"
            
            latex_content.append(f"{title} & {author} & {video} \\\\")
            latex_content.append(r'\hline')
        
        latex_content.extend([
            r'\end{longtable}',
            '',
            f"\\textit{{Total books found: {results['books_found']}}}",
            '',
            r'\end{document}'
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(latex_content))
        
        print(f"LaTeX export saved to: {output_file}")
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        replacements = {
            '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
            '_': r'\_', '{': r'\{', '}': r'\}',
            '~': r'\textasciitilde{}', '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text
    
    def export_to_json(self, results: Dict, output_file: str = 'books_export.json'):
        """Export results to JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"JSON export saved to: {output_file}")


def analyze_channels_from_csv(csv_file: str, api_key: str, output_dir: str = './'):
    """Analyze all YouTube channels from a CSV file"""
    extractor = YouTubeBookExtractor(api_key)
    all_results = {}
    all_books = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        channels = list(reader)
    
    print(f"Found {len(channels)} channels to analyze\n")
    
    for i, channel in enumerate(channels, 1):
        channel_id = channel['Channel Id']
        channel_title = channel['Channel Title']
        
        print(f"\n[{i}/{len(channels)}] Analyzing: {channel_title}")
        
        try:
            results = extractor.analyze_channel(channel_id)
            
            if 'error' not in results:
                all_results[channel_title] = results
                
                for book in results['books']:
                    book['channel'] = channel_title
                    all_books.append(book)
                
                print(f"✓ Found {results['books_found']} books")
            else:
                print(f"✗ Error: {results['error']}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ Exception: {e}")
            continue
    
    # Save JSON
    output_file = f'{output_dir}/all_books.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_channels': len(all_results),
            'total_books': len(all_books),
            'channels': all_results,
            'all_books': all_books
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Channels analyzed: {len(all_results)}")
    print(f"Total books found: {len(all_books)}")
    print(f"Output saved to: {output_file}")
    
    return all_results, all_books


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("YouTube Book Extractor")
    print("=" * 60)
    
    # REPLACE THIS WITH YOUR ACTUAL API KEY
    API_KEY = os.environ.get("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
    
    # Choose your analysis mode:
    
    # MODE 1: Analyze single channel (Huberman Lab)
    print("\nMode 1: Analyzing Huberman Lab channel...")
    extractor = YouTubeBookExtractor(API_KEY)
    results = extractor.analyze_channel("@hubermanlab")
    
    if 'error' not in results:
        print(f"\n{'='*50}")
        print(f"Analysis Complete!")
        print(f"Total videos analyzed: {results['total_videos']}")
        print(f"Books found: {results['books_found']}")
        print(f"{'='*50}\n")
        
        # Print first 10 books
        print("Sample books found:")
        for i, book in enumerate(results['books'][:10], 1):
            print(f"{i}. {book['title']}")
            if book['author'] != 'Unknown':
                print(f"   Author: {book['author']}")
            if book.get('link'):
                print(f"   Link: {book['link']}")
            print()
        
        # Export results
        extractor.export_to_json(results, "huberman_books.json")
        extractor.export_to_latex(results, "huberman_books.tex")
    
    # MODE 2: Batch analyze from CSV (uncomment to use)
    # print("\nMode 2: Batch analyzing channels from CSV...")
    # analyze_channels_from_csv("youtube_channels.csv", API_KEY, output_dir='./')
