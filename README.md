# YouTube Audio Collector

YouTube Audio Collector is a Python script that downloads audio from specified YouTube channels, extracts captions, and creates a dataset of audio chunks with corresponding transcriptions. It's particularly designed to collect audio segments that contain both Arabic and English text.

## Features

- Downloads audio from multiple YouTube channels
- Extracts manually created captions
- Cuts audio into chunks based on caption timing
- Creates a dataset with audio files and corresponding transcriptions
- Pushes the created dataset to Hugging Face Hub

## Requirements

- Python 3.7+
- FFmpeg (for audio processing)

## Installation

1. Clone this repository:
```
https://github.com/MohamedAliRashad/youtube-audio-collector.git
cd youtube-audio-collector
```

2. Install the required Python packages:
```
pip install -r requirements.txt
```

3. Install FFmpeg (if not already installed):
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- macOS (with Homebrew): `brew install ffmpeg`
- Windows: Download from the [official FFmpeg website](https://ffmpeg.org/download.html) and add to PATH

## Usage

1. Create a text file with YouTube channel URLs, one per line.

2. Run the script with the following command:
```
python youtube_audio_collector.py --output_dir my_audio_dir --urls_file channel_urls.txt --hub_dataset_name my-dataset --private
```

Arguments:
- `--output_dir`: Directory to save audio files (default: 'audio')
- `--urls_file`: File containing YouTube channel URLs
- `--hub_dataset_name`: Name of the dataset on Hugging Face Hub
- `--private`: Flag to push the dataset as private (optional)

## How it works

1. The script reads YouTube channel URLs from the specified file.
2. For each video in each channel:
- It checks for manually created captions containing both Arabic and English text.
- If suitable captions are found, it downloads the audio.
- The audio is then cut into chunks based on the caption timing.
3. Audio chunks and their corresponding transcriptions are saved.
4. A dataset is created from the collected audio and captions.
5. The dataset is pushed to the Hugging Face Hub.

## Note

This script is designed for research and educational purposes. Ensure you comply with YouTube's terms of service and respect copyright laws when using this tool.

## License

[MIT License](LICENSE)

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/yourusername/youtube-audio-collector/issues) if you want to contribute.