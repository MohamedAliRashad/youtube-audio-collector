from pytubefix import YouTube, Channel
from youtube_transcript_api import YouTubeTranscriptApi
import re
from datasets import load_dataset, Audio, Dataset
from pydub import AudioSegment
from tqdm import tqdm
import pandas as pd
from pathlib import Path
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process YouTube channels for audio and captions.")
    parser.add_argument('--output_dir', type=str, default='audio', help='Output directory for audio files')
    parser.add_argument('--urls_file', type=str, help='File containing YouTube channel URLs')
    parser.add_argument('--hub_dataset_name', type=str, default='arabic-english-code-switching', help='Name of the dataset on Hugging Face Hub')
    parser.add_argument('--private', action='store_true', help='Push dataset as private')
    return parser.parse_args()

args = parse_arguments()

df = pd.DataFrame(columns=["file_name", "sentence"])

output_path = Path(args.output_dir)
output_path.mkdir(exist_ok=True, parents=True)
metadata_path = output_path / "metadata.jsonl"


def get_manual_captions(video_id):
    try:
        # Fetch the available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Get the manually created transcript
        transcript = transcript_list.find_manually_created_transcript(["ar"])

        # Fetch the transcript data
        caption_data = transcript.fetch()

    except Exception as e:
        return None

    # Arabic Unicode range
    arabic_pattern = re.compile(r"[\u0600-\u06FF]+")

    # English pattern (simple a-z or A-Z)
    english_pattern = re.compile(r"[a-zA-Z]+")

    arabic_and_english_captions = []
    for caption in caption_data:
        text = caption["text"]
        if arabic_pattern.search(text) and english_pattern.search(text):
            arabic_and_english_captions.append(caption)

    if len(arabic_and_english_captions) > 0:
        return arabic_and_english_captions
    else:
        return None


def cut_audio(audio_path, captions):
    audio = AudioSegment.from_file(audio_path)
    audio_chunks = []
    for caption in captions:
        start = caption["start"]
        duration = caption["duration"]
        end = start + duration
        audio_chunk = audio[start * 1000 : end * 1000]
        audio_chunks.append(audio_chunk)
    return audio_chunks

# Load URLs from file
with open(args.urls_file, 'r') as file:
    urls = [line.strip() for line in file]
urls = list(set(urls))

for url in tqdm(urls):
    channel = Channel(url)
    for video in tqdm(channel.videos, leave=False):
        subtitles = get_manual_captions(video.video_id)
        if subtitles:
            try:
                # Download audio
                yt = YouTube(f"https://www.youtube.com/watch?v={video.video_id}")
                audio_abrs = list(
                    set(
                        [
                            stream.abr
                            for stream in yt.streams.filter(only_audio=True)
                            if stream.abr is not None
                        ]
                    )
                )
                audio_abrs = sorted([int(abr.strip("kbps")) for abr in set(audio_abrs)])
                audio_abrs = [f"{abr}kbps" for abr in audio_abrs]
                audio_stream = yt.streams.filter(
                    only_audio=True, abr=audio_abrs[-1]
                ).first()
                audio_path = audio_stream.download(
                    output_path=str(output_path),
                    filename=f"{video.video_id}.{audio_stream.subtype}",
                )

                # Cut audio into chunks
                audio_chunks = cut_audio(audio_path, subtitles)
                print(f"Downloaded {len(audio_chunks)} audio chunks for {video.video_id}")
            except Exception as e:
                print(f"Failed with {video.video_id}: {e}")
                Path(audio_path).unlink()
                continue

            # Save audio chunks to disk and update DataFrame
            for chunk, caption in zip(audio_chunks, subtitles):
                output_filename = f"{output_path}/{video.video_id}_{caption['start']}.wav"
                chunk.export(output_filename, format="wav")
                df = df._append(
                    {
                        "file_name": f"{video.video_id}_{caption['start']}.wav",
                        "sentence": caption["text"].strip().strip('"').strip("'"),
                    },
                    ignore_index=True,
                )
                df.to_json(
                    metadata_path, orient="records", lines=True, force_ascii=False
                )
            Path(audio_path).unlink()
        else:
            print("No subtitles with both Arabic and English in it found.")

# Create a new dataset with the new entries
new_ds = load_dataset("audiofolder", data_dir=str(output_path), split="train")
new_ds = new_ds.cast_column("audio", Audio(sampling_rate=16000))

# Drop duplicates & Shuffle
new_ds = new_ds.to_pandas().drop_duplicates(subset=['sentence']).reset_index(drop=True)
new_ds = Dataset.from_pandas(new_ds).cast_column("audio", Audio(sampling_rate=16000))
new_ds = new_ds.shuffle()

# Save the combined dataset
new_ds.push_to_hub(args.hub_dataset_name, private=args.private, num_shards=3)
