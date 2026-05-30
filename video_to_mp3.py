# Converts local videos or YouTube links to mp3 
import os 
import subprocess
import re
import sys

# Reconfigure stdout/stderr to utf-8 to prevent charmap/unicode errors when printing emoji titles on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Try importing yt_dlp; if not present, we will notify the user when they try to use YouTube mode.
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

def clean_filename(name):
    # Remove characters that might be problematic for filenames
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', " ", cleaned)
    return cleaned.strip()

def parse_range(range_str, total):
    """
    Parses a range string like '1-3', '5', '1,2,5' and returns a list of 0-based indices.
    """
    if not range_str.strip():
        return list(range(total))
    
    indices = set()
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-')
                start_idx = int(start) - 1
                end_idx = int(end) - 1
                start_idx = max(0, start_idx)
                end_idx = min(total - 1, end_idx)
                for i in range(start_idx, end_idx + 1):
                    indices.add(i)
            except ValueError:
                pass
        else:
            try:
                idx = int(part) - 1
                if 0 <= idx < total:
                    indices.add(idx)
            except ValueError:
                pass
    return sorted(list(indices))

def process_local_videos():
    if not os.path.exists("videos"):
        os.makedirs("videos")
    if not os.path.exists("audios"):
        os.makedirs("audios")

    files = os.listdir("videos")
    # Filter only files (ignore directories)
    files = [f for f in files if os.path.isfile(os.path.join("videos", f))]
    
    if not files:
        print("No videos found in the 'videos' directory.")
        return

    print(f"Found {len(files)} files in 'videos/'. Processing...")
    for idx, file in enumerate(files, start=1):
        try:
            # Safely extract tutorial number and name
            if " [" in file and " #" in file:
                tutorial_number = file.split(" [")[0].split(" #")[1]
            else:
                tutorial_number = str(idx)
            
            if " ｜ " in file:
                file_name = file.split(" ｜ ")[0]
            else:
                file_name = os.path.splitext(file)[0]
        except Exception as e:
            tutorial_number = str(idx)
            file_name = os.path.splitext(file)[0]

        tutorial_number = clean_filename(tutorial_number)
        file_name = clean_filename(file_name)
        
        input_path = f"videos/{file}"
        output_path = f"audios/{tutorial_number}_{file_name}.mp3"
        
        print(f"Converting: {input_path} -> {output_path}")
        # Run ffmpeg with -y to overwrite existing files if needed
        subprocess.run(["ffmpeg", "-y", "-i", input_path, output_path])

def download_youtube():
    if yt_dlp is None:
        print("Error: 'yt-dlp' is not installed in the python environment.")
        print("Please run: venv\\Scripts\\pip install yt-dlp")
        return

    if not os.path.exists("audios"):
        os.makedirs("audios")

    url = input("Enter YouTube video/playlist URL, or path to text file containing URLs: ").strip()
    if not url:
        print("No URL provided.")
        return

    # Determine if input is a text file containing multiple URLs
    urls = []
    if os.path.exists(url) and os.path.isfile(url):
        with open(url, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        print(f"Loaded {len(urls)} URLs from file.")
    else:
        urls = [url]

    # Extract all video entries from the provided URLs
    all_entries = []
    
    ydl_opts_flat = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    print("\nRetrieving metadata. Please wait...")
    with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
        for u in urls:
            try:
                info = ydl.extract_info(u, download=False)
                if 'entries' in info:
                    # Playlist
                    playlist_title = info.get('title', 'Playlist')
                    print(f"Found playlist: {playlist_title}")
                    for entry in info['entries']:
                        if entry:
                            # Build complete watch URL if flat extraction only returned ID
                            entry_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                            all_entries.append({
                                'url': entry_url,
                                'title': entry.get('title')
                            })
                else:
                    # Single video
                    all_entries.append({
                        'url': u,
                        'title': info.get('title')
                    })
            except Exception as e:
                print(f"Error fetching metadata for {u}: {e}")

    total_videos = len(all_entries)
    if total_videos == 0:
        print("No valid videos or playlists found to download.")
        return

    print(f"Found {total_videos} videos in total.")
    
    # Range selection if multiple videos found
    indices_to_download = list(range(total_videos))
    if total_videos > 1:
        range_str = input("Enter playlist items to download (e.g. 1-3, 5, or leave blank to download all): ").strip()
        indices_to_download = parse_range(range_str, total_videos)
        if not indices_to_download:
            print("No items selected for download.")
            return
        print(f"Selected {len(indices_to_download)} items out of {total_videos} for download.")

    start_num_str = input("Enter starting tutorial number (default 1): ").strip()
    start_num = int(start_num_str) if start_num_str.isdigit() else 1

    for run_idx, idx in enumerate(indices_to_download):
        current_num = start_num + run_idx
        entry = all_entries[idx]
        video_url = entry['url']
        raw_title = entry['title'] or f"video_{current_num}"
        cleaned_title = clean_filename(raw_title)
        
        output_filename = f"audios/{current_num}_{cleaned_title}"
        final_mp3_path = f"{output_filename}.mp3"
        
        print(f"\n[{run_idx+1}/{len(indices_to_download)}] Processing Video: {raw_title}")
        print(f"URL: {video_url}")
        print(f"Target path: {final_mp3_path}")

        dl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_filename + '.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([video_url])
            print(f"Successfully finished processing: {final_mp3_path}")
        except Exception as e:
            print(f"Failed to process video {raw_title}. Error: {e}")

def main():
    print("=== RAG Teaching Assistant Ingestion Pipeline ===")
    print("1. Process local video files in 'videos/' directory")
    print("2. Download and convert YouTube video/playlist URL directly")
    choice = input("Select an option (1 or 2): ").strip()
    
    if choice == "1":
        process_local_videos()
    elif choice == "2":
        download_youtube()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()