# RAG Pipeline YouTube Integration Plan

This plan details how we will modify the RAG pipeline to accept YouTube URLs (single videos or playlists) directly. It leverages `yt-dlp` to download audio directly and format it for the downstream whisper transcription and embedding scripts.

## Proposed Changes

We will modify `video_to_mp3.py` to support two modes of operation:
1. **YouTube Mode**: Downloads audio directly from a YouTube video URL, playlist URL, or a list of URLs from a text file, saving them as `[number]_[title].mp3` in the `audios/` folder.
2. **Local Mode (Existing)**: Processes existing video files in the `videos/` folder, with robust file name parsing to prevent the `IndexError` when titles do not match the expected pattern.

### Dependencies
- **yt-dlp**: We will install `yt-dlp` in the virtual environment.
- **ffmpeg**: Assumed to be installed on the system (required by `yt-dlp` and Whisper).

---

### Pipeline Component

#### [MODIFY] [video_to_mp3.py](file:///c:/Users/nilesh/nisarg-project/RAG_AI_TEACHING_ASSISTANT/video_to_mp3.py)

We will rewrite `video_to_mp3.py` to:
- Prompt the user to select whether they want to process **Local Videos** or download from **YouTube**.
- Under **YouTube Mode**:
  - Prompt for a YouTube URL (playlist, video, or link) or a file containing links.
  - Prompt for a starting index/number (e.g. `1` or `101`) to number the downloaded files sequentially.
  - Download only the audio and convert it to mp3 using `yt-dlp`'s python interface or subprocess, saving it as `audios/{number}_{title}.mp3`.
- Under **Local Mode**:
  - Keep the existing functionality but make the filename parser robust. If the `" #"` or `" ["` delimiters are missing, fallback to sequential numbering or clean the name safely.

Here is the proposed logic for `video_to_mp3.py`:

```python
import os
import subprocess
import re

def clean_filename(name):
    # Remove characters that might be problematic for filenames
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def process_local_videos():
    if not os.path.exists("videos"):
        os.makedirs("videos")
    if not os.path.exists("audios"):
        os.makedirs("audios")

    files = os.listdir("videos")
    if not files:
        print("No videos found in the 'videos' directory.")
        return

    for idx, file in enumerate(files, start=1):
        # Existing logic with robustness checks
        try:
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
        
        print(f"Processing local: {tutorial_number} - {file_name}")
        subprocess.run(["ffmpeg", "-y", "-i", f"videos/{file}", f"audios/{tutorial_number}_{file_name}.mp3"])

def download_youtube():
    if not os.path.exists("audios"):
        os.makedirs("audios")

    url = input("Enter YouTube video URL, playlist URL, or path to text file containing URLs: ").strip()
    if not url:
        print("No URL provided.")
        return

    # Check if input is a text file containing multiple URLs
    urls = []
    if os.path.exists(url) and os.path.isfile(url):
        with open(url, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        print(f"Found {len(urls)} URLs in the file.")
    else:
        urls = [url]

    start_num_str = input("Enter starting tutorial number (default 1): ").strip()
    start_num = int(start_num_str) if start_num_str.isdigit() else 1

    print("\nStarting downloads. This might take a few minutes...")
    
    # We will use yt-dlp to download and convert to mp3
    # Use python's subprocess to run yt-dlp command.
    # We download audio only (-x) and convert to mp3 (--audio-format mp3)
    # Output template: we can let yt-dlp download, then rename, or download directly.
    # Since yt-dlp outputs to a temp template, we can download and rename it programmatically to ensure it fits our '{number}_{title}.mp3' format perfectly.
    
    for idx, video_url in enumerate(urls):
        current_num = start_num + idx
        print(f"\n[{idx+1}/{len(urls)}] Processing: {video_url}")
        
        # 1. Get video title first using yt-dlp --get-title
        title_cmd = ["yt-dlp", "--get-title", "--no-warnings", video_url]
        try:
            title_res = subprocess.run(title_cmd, capture_output=True, text=True, check=True)
            raw_title = title_res.stdout.strip()
            title = clean_filename(raw_title)
        except Exception as e:
            print(f"Warning: Could not fetch title. Using default title. Error: {e}")
            title = f"youtube_video_{current_num}"

        output_filename = f"audios/{current_num}_{title}.mp3"
        print(f"Title: {title}")
        print(f"Target: {output_filename}")
        
        # 2. Download and convert to mp3
        # We specify -o to a temporary file name, and yt-dlp will automatically convert it to mp3
        temp_template = f"audios/temp_{current_num}.%(ext)s"
        dl_cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", temp_template,
            video_url
        ]
        
        try:
            subprocess.run(dl_cmd, check=True)
            # yt-dlp will produce 'audios/temp_[current_num].mp3'
            temp_mp3 = f"audios/temp_{current_num}.mp3"
            if os.path.exists(temp_mp3):
                if os.path.exists(output_filename):
                    os.remove(output_filename)
                os.rename(temp_mp3, output_filename)
                print(f"Successfully downloaded and saved: {output_filename}")
            else:
                print(f"Error: Expected audio file {temp_mp3} was not found.")
        except Exception as e:
            print(f"Failed to download/convert video: {video_url}. Error: {e}")

def main():
    print("=== RAG Teaching Assistant Audio Ingestion ===")
    print("1. Process local video files in 'videos/' directory")
    print("2. Download audio from YouTube video/playlist URL")
    choice = input("Select an option (1 or 2): ").strip()
    
    if choice == "1":
        process_local_videos()
    elif choice == "2":
        # Make sure yt-dlp is installed or prompt
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True)
        except FileNotFoundError:
            print("yt-dlp is not installed or not in PATH.")
            print("Please run: venv\\Scripts\\pip install yt-dlp")
            return
        download_youtube()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
```

## Verification Plan

### Automated/Local Tests
1. **Dependency Verification**: Run `venv\Scripts\pip install yt-dlp` to ensure yt-dlp is installed inside the virtual environment.
2. **Local Mode Check**: Test local video files with titles that have other formats (like no ` #` or no ` [`) to ensure no `IndexError` occurs.
3. **YouTube Mode Check**:
   - Run the modified `video_to_mp3.py` with a sample YouTube video link.
   - Verify that the resulting file is saved under `audios/1_[Title].mp3`.
   - Run the subsequent `mp3_to_json.py` and `preprocess_json.py` steps to verify the entire pipeline runs without modification.
