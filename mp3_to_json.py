import whisper
import json
import os
import sys

# Reconfigure stdout/stderr to utf-8 to prevent console output emoji errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure output directory exists
if not os.path.exists("jsons"):
    os.makedirs("jsons")

# Load model lazily (only if we have files to transcribe)
model = None

audios = os.listdir("audios")

# Filter files that actually need transcription
files_to_transcribe = []
for audio in audios:
    if "_" in audio and audio.endswith(".mp3"):
        json_path = f"jsons/{audio}.json"
        
        # Smart check: if number is single digit (e.g. "1"), check if zero-padded json (e.g. "01") exists
        parts = audio.split("_", 1)
        padded_json_exists = False
        if len(parts) > 1 and parts[0].isdigit() and len(parts[0]) == 1:
            padded_audio_name = f"0{parts[0]}_{parts[1]}"
            padded_json_path = f"jsons/{padded_audio_name}.json"
            if os.path.exists(padded_json_path):
                padded_json_exists = True

        if os.path.exists(json_path) or padded_json_exists:
            print(f"Skipping already transcribed file: {audio}")
            continue
            
        files_to_transcribe.append(audio)

if not files_to_transcribe:
    print("No new audio files to transcribe.")
    sys.exit(0)

# Whisper model selection. 'small' or 'medium' are recommended for CPU-only systems with <= 8GB RAM.
# 'large-v2' requires ~10GB of RAM/VRAM to load, which causes MemoryError on this system.
PREFERRED_MODEL = "small" 

print(f"Preparing to transcribe {len(files_to_transcribe)} files...")
model_options = [PREFERRED_MODEL, "small", "base", "tiny"]

# Remove duplicates while preserving order
seen = set()
models_to_try = [x for x in model_options if not (x in seen or seen.add(x))]

for model_name in models_to_try:
    try:
        print(f"Loading Whisper model '{model_name}'...")
        model = whisper.load_model(model_name)
        print(f"Successfully loaded '{model_name}'.")
        break
    except (MemoryError, RuntimeError) as e:
        print(f"Failed to load Whisper model '{model_name}' due to memory limits: {e}")
        print("Retrying with a smaller model...")

if not model:
    print("Error: Failed to load any Whisper model due to memory constraints.")
    sys.exit(1)

for audio in files_to_transcribe:
    parts = audio.split("_", 1)
    number = parts[0]
    title = parts[1][:-4]
    print(f"Transcribing {number}: {title}...")
    
    try:
        result = model.transcribe(
            audio=f"audios/{audio}",
            language="hi",
            task="translate",
            word_timestamps=False
        )
        
        chunks = []
        for segment in result["segments"]:
            chunks.append({
                "number": number,
                "title": title,
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            })
        
        chunks_with_metadata = {"chunks": chunks, "text": result["text"]}

        with open(f"jsons/{audio}.json", "w", encoding="utf-8") as f:
            json.dump(chunks_with_metadata, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved transcription: jsons/{audio}.json")
    except Exception as e:
        print(f"Failed to transcribe {audio}. Error: {e}")