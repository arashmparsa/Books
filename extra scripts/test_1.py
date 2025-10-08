"""
Huberman Lab Specific Book Extractor
Targets the exact format: "Book Title": Amazon_link
"""

import re
import json
from typing import List, Dict
import time
from googleapiclient.discovery import build

class HubermanBookExtractor:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    def get_channel_videos(self, channel_handle: str) -> List[Dict]:
        """Get all videos from Huberman Lab channel"""
        username = channel_handle.replace('@', '')
        
        # Get channel ID
        request = self.youtube.search().list(
            part="snippet", q=username, type="channel", maxResults=1
        )
        response = request.execute()
        channel_id = response['items'][0]['snippet']['channelId']
        
        # Get uploads playlist
        request = self.youtube.channels().list(part="contentDetails", id=channel_id)
        response = request.execute()
        playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get all video IDs
        video_ids = []
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
        
        print(f"Found {len(video_ids)} videos")
        
        # Get video details
        videos = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            request = self.youtube.videos().list(part="snippet", id=','.join(batch))
            response = request.execute()
            videos.extend(response['items'])
            time.sleep(0.1)
            
            if (i + 50) % 200 == 0:
                print(f"Processed {i + 50} videos...")
        
        return videos
    
    def extract_books_huberman_format(self, description: str, video_title: str) -> List[Dict]:
        """Extract books using MULTIPLE patterns for maximum coverage"""
        books = []
        seen_titles = set()
        
        # PATTERN 1: Huberman's quoted format: "Book Title": link
        # Handle both straight quotes ("") and curly quotes ("")
        quoted_patterns = [
            r'"([^"]{5,150})":\s*(https?://(?:www\.)?(?:amazon\.com|amzn\.to)/[\w\-/]+)',
            r'"([^"]{5,150})":\s*(https?://(?:www\.)?(?:amazon\.com|amzn\.to)/[\w\-/]+)',
            r'["""]([^"""]{5,150})["""]:\s*(https?://(?:www\.)?(?:amazon\.com|amzn\.to)/[\w\-/]+)',
        ]
        
        for pattern in quoted_patterns:
            matches = re.findall(pattern, description)
            for title, link in matches:
                title = title.strip()
                if title.lower() not in seen_titles and len(title) > 5:
                    books.append({
                        'title': title,
                        'author': self._extract_author(description, title),
                        'link': link,
                        'video_title': video_title
                    })
                    seen_titles.add(title.lower())
        
        # PATTERN 2: Amazon links with nearby text (original method)
        amazon_links = re.findall(r'(https?://(?:www\.)?(?:amazon\.com|amzn\.to)/[\w\-/]+)', description)
        
        for link in amazon_links:
            # Skip if we already found this link in pattern 1
            if any(book['link'] == link for book in books):
                continue
            
            # Get context around the link
            link_pos = description.find(link)
            context_start = max(0, link_pos - 200)
            context_end = min(len(description), link_pos + 200)
            context = description[context_start:context_end]
            
            # Look for book title in context
            title = None
            
            # Try to find text before the link
            before_link = context[:link_pos - context_start]
            
            # Look for capitalized title-like text
            title_patterns = [
                r'([A-Z][A-Za-z\s:,&\'\-]{10,120})(?=\s*:?\s*https?://)',
                r'-\s*([A-Z][^\n\-:]{10,100})\s*:',
                r'\n([A-Z][^\n:]{10,100})\s*:',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, before_link)
                if match:
                    potential_title = match.group(1).strip()
                    # Filter junk
                    skip = ['click', 'here', 'check out', 'visit', 'subscribe', 'watch', 'listen']
                    if not any(word in potential_title.lower() for word in skip):
                        title = potential_title
                        break
            
            if title and title.lower() not in seen_titles:
                books.append({
                    'title': title,
                    'author': self._extract_author(context, title),
                    'link': link,
                    'video_title': video_title
                })
                seen_titles.add(title.lower())
        
        return books
    
    def _extract_author(self, text: str, title: str) -> str:
        """Extract author name from text near the book title"""
        # Look for author patterns
        author_patterns = [
            r'by\s+([A-Z][a-zA-Z\.\s]{3,40})',
            r'author:\s*([A-Z][a-zA-Z\.\s]{3,40})',
            r'([A-Z][a-zA-Z\.\s]{3,40}),?\s+(?:Ph\.?D\.?|MD|professor)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                author = match.group(1).strip()
                # Clean up
                author = re.split(r'[,\n\(]', author)[0].strip()
                if len(author) > 3 and len(author) < 50:
                    return author
        
        return "Unknown"
    
    def analyze_channel(self, channel_handle: str) -> Dict:
        """Extract all books from Huberman Lab"""
        print(f"Analyzing Huberman Lab channel...")
        
        videos = self.get_channel_videos(channel_handle)
        
        print(f"Extracting books from {len(videos)} videos...")
        all_books = []
        
        for video in videos:
            description = video['snippet']['description']
            title = video['snippet']['title']
            books = self.extract_books_huberman_format(description, title)
            all_books.extend(books)
        
        # Deduplicate
        unique_books = {}
        for book in all_books:
            key = book['title'].lower().strip()
            if key not in unique_books:
                unique_books[key] = book
        
        books_list = sorted(unique_books.values(), key=lambda x: x['title'])
        
        return {
            'total_videos': len(videos),
            'books_found': len(books_list),
            'books': books_list
        }
    
    def export_to_json(self, results: Dict, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved: {filename}")
    
    def export_to_latex(self, results: Dict, filename: str):
        """Export to clean LaTeX table"""
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
            r'\section{Huberman Lab Book Recommendations}',
            '',
            r'\begin{longtable}{|p{8cm}|p{4cm}|p{2.5cm}|}',
            r'\hline',
            r'\textbf{Book Title} & \textbf{Author} & \textbf{Link} \\',
            r'\hline',
        ]
        
        for book in results['books']:
            title = escape_latex(book['title'])
            author = escape_latex(book['author'])
            link = r'\href{' + book['link'] + r'}{Amazon}'
            
            latex.append(f"{title} & {author} & {link} \\\\")
            latex.append(r'\hline')
        
        latex.extend([
            r'\end{longtable}',
            '',
            f"\\textit{{Total books: {results['books_found']}}}",
            r'\end{document}'
        ])
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(latex))
        print(f"✓ Saved: {filename}")
    
    def export_to_txt(self, results: Dict, filename: str):
        """Export to readable text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("HUBERMAN LAB BOOK RECOMMENDATIONS\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total videos analyzed: {results['total_videos']}\n")
            f.write(f"Total books found: {results['books_found']}\n\n")
            f.write("="*80 + "\n\n")
            
            for i, book in enumerate(results['books'], 1):
                f.write(f"{i}. {book['title']}\n")
                f.write(f"   Author: {book['author']}\n")
                f.write(f"   Link: {book['link']}\n")
                f.write(f"   From: {book['video_title'][:70]}...\n\n")
        
        print(f"✓ Saved: {filename}")


# RUN EXTRACTION
if __name__ == "__main__":
    API_KEY = "AIzaSyAUywIjr2B4gDBvWKZnx8aMA-luPPuxRZk"
    
    print("\n" + "="*80)
    print("HUBERMAN LAB BOOK EXTRACTOR")
    print("Using format: \"Book Title\": Amazon_link")
    print("="*80 + "\n")
    
    extractor = HubermanBookExtractor(API_KEY)
    results = extractor.analyze_channel("@hubermanlab")
    
    # Display results
    print("\n" + "="*80)
    print(f"EXTRACTION COMPLETE!")
    print("="*80)
    print(f"Videos analyzed: {results['total_videos']}")
    print(f"Books found: {results['books_found']}")
    print("="*80 + "\n")
    
    # Show all books
    print("BOOKS FOUND:\n")
    for i, book in enumerate(results['books'], 1):
        print(f"{i}. {book['title']}")
        if book['author'] != "Unknown":
            print(f"   Author: {book['author']}")
        print(f"   Link: {book['link']}")
        print()
    
    # Export to multiple formats
    extractor.export_to_json(results, "huberman_books_final.json")
    extractor.export_to_latex(results, "huberman_books_final.tex")
    extractor.export_to_txt(results, "huberman_books_final.txt")
    
    print("\n" + "="*80)
    print("FILES CREATED:")
    print("="*80)
    print("  📄 huberman_books_final.txt   - Easy to read list")
    print("  📊 huberman_books_final.json  - Structured data")
    print("  📝 huberman_books_final.tex   - LaTeX document")
    print("="*80 + "\n")
