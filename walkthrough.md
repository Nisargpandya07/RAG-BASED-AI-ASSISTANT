# RAG Teaching Assistant Ingestion Pipeline Walkthrough

We have integrated YouTube download capabilities into the RAG Teaching Assistant pipeline. The steps outlined in your `Readme.md` now work with both local files and direct YouTube links.

Below is a walkthrough of how each step of the pipeline functions after our updates:

---

## 📋 Updated Workflow Mapping

### 1. Ingestion / Download Phase (`video_to_mp3.py`)
Instead of manually downloading videos to the `videos/` folder, you can run `video_to_mp3.py` which now supports two options:

- **Option 1 (Local Videos)**: Converts files from the `videos/` folder using `ffmpeg`. We fixed the `IndexError` bug by adding robust filename splitting so it won't crash if titles don't contain `" #"` or `" ["`.
- **Option 2 (YouTube Downloader)**: Downloads audio directly from a YouTube video URL, playlist URL (like the Sigma Web Development playlist), or a text file of URLs.
  - Emojis in titles (e.g. `🗿`) are fully supported without causing console encoding crashes.
  - You can select a **range of videos** from a playlist to download (e.g., download just items `1-3` or `5` instead of the whole playlist of 139 videos).
  - You can customize the **starting tutorial number** (e.g., start naming files from `1` or `101`).
  - Saves the audio files directly in the `audios/` folder as `[number]_[title].mp3`.

### 2. Transcription Phase (`mp3_to_json.py`)
Converts mp3 files in the `audios/` folder to text and time-chunked transcripts in the `jsons/` folder.
- **Resource/Memory Optimization**: Since running on CPU with 8GB RAM is limited, we replaced the heavy `'large-v2'` model (which causes a `MemoryError` during loading) with a smaller, CPU-friendly model (`'small'`).
- **Robust Fallback Loader**: Added automatic detection and fallback mechanism. If loading the preferred model runs out of memory, it catches the error and retries with progressively smaller models (`'small' -> 'base' -> 'tiny'`).
- **Redundancy Protection**: The script checks the `jsons/` folder and **skips already-transcribed files**. If you download new videos, running the script will only transcribe the new files, saving hours of CPU computation.
- **Smart Padding Matching**: It automatically maps single-digit files (e.g., `1_...`) with zero-padded JSON files (e.g., `01_...`) to ensure existing transcriptions are detected correctly.

### 3. Embedding Phase (`preprocess_json.py`)
Converts the transcribed JSON chunks into embeddings via Ollama and saves them to `embeddings.joblib`. This step works exactly as before since the output schema of the JSON files remains identical.

### 4. Query Phase (`process_incoming.py`)
Performs cosine similarity search against the embeddings database and queries the LLM. This step works exactly as before.

---

## 🧪 Verification Results

We verified the YouTube download step by downloading the first tutorial of the CodeWithHarry Sigma Web Development Course:
- **Selected Playlist**: `https://youtube.com/playlist?list=PLu0W_9lII9agq5TrH9XLIKQvv0iaF2X3w&si=I91Ov67B4aSXCBfw`
- **Output File**: Saved directly as `audios/1_Installing VS Code & How Websites Work Sigma Web Development Course - Tutorial #1.mp3`.
- **Format**: Decoded to `.mp3` automatically using `ffmpeg` post-processing.
- **Downstream Compatibility**: The file prefix `1_...` matches the split format of the transcription script.
