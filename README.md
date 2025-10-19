# VideoLib

**Video Processing Library for Python**

A comprehensive Python library for video downloading (from direct URLs), splitting, and clipping operations with FFmpeg integration. VideoLib provides a clean, object-oriented interface for common video processing tasks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)

## Features

- 🎬 **Video Downloading**: Download videos from direct URLs and streaming protocols using FFmpeg
- ✂️ **Video Splitting**: Split large videos into smaller segments by file size
- 🎞️ **Video Clipping**: Extract specific time intervals from videos
- ⚙️ **FFmpeg Integration**: Powerful FFmpeg/FFprobe wrapper with clean Python API
- 📦 **Batch Processing**: Process multiple videos with JSON configuration
- 🔧 **Flexible Configuration**: Extensive customization options for all operations
- 🚀 **Performance**: Efficient processing with stream copying (no re-encoding)

## Installation

### Prerequisites

**FFmpeg** is required and must be installed separately:

- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **Linux**: `sudo apt-get install ffmpeg`
- **macOS**: `brew install ffmpeg`

### Install from GitHub

```bash
pip install git+https://github.com/BrianAtCode/videolib.git
```

### Install from Source

```bash
git clone https://github.com/BrianAtCode/videolib.git
cd videolib
pip install -e .
```

## Quick Start

### Download a Video

```python
from videolib import download_video

# Download from direct URL (works with HTTP/HTTPS streaming)
result = download_video(
    url="https://example.com/video.mp4",
    output_name="my_video",
    output_extension="mp4"
)

if result.success:
    print(f"Downloaded: {result.output_file}")
```

**Supported URL types:**
- Direct video files (HTTP/HTTPS)
- Streaming protocols (HLS/M3U8, RTSP, RTMP)
- Network streams

**Note**: For YouTube and platform-specific videos, use [yt-dlp](https://github.com/yt-dlp/yt-dlp) as a separate tool first to get the direct video URL.

### Split Video by Size

```python
from videolib import split_video_by_size

# Split a 2GB video into 500MB segments
result = split_video_by_size(
    source_file="large_video.mp4",
    target_size_mb=500,
    output_name="segment",
    output_extension="mp4"
)

if result.success:
    print(f"Created {len(result.output_files)} segments")
```

### Create Video Clips

```python
from videolib import clip_video_segments

# Extract multiple clips from a video
result = clip_video_segments(
    source_file="movie.mp4",
    intervals=[
        (30, 90),      # 30s to 90s
        (120, 180),    # 2:00 to 3:00
        (300, 450)     # 5:00 to 7:30
    ],
    output_name="clip",
    output_extension="mp4"
)

if result.success:
    print(f"Created {len(result.output_files)} clips")
```

## Advanced Usage

### Using the Video Processor

```python
from videolib import VideoProcessor, ProcessorConfig

# Create processor with custom configuration
config = ProcessorConfig(
    temp_dir="./temp",
    delete_source_after_split=False,
    enable_gpu=True
)

processor = VideoProcessor(config)

# Get video information
media_info = processor.get_media_info("video.mp4")
print(f"Duration: {media_info.duration}s")
print(f"Size: {media_info.size_bytes} bytes")
print(f"Video Codec: {media_info.video_codec}")
print(f"Audio Codec: {media_info.audio_codec}")
```

### Batch Processing with Configuration

```python
from videolib import ConfigurationManager

# Load batch processing configuration
config_manager = ConfigurationManager()
config = config_manager.load_from_file("config.json")

# Process all tasks
processor = VideoProcessor()
results = processor.process_batch(config.tasks)

# Check results
for i, result in enumerate(results):
    if result.success:
        print(f"Task {i+1}: Success - {len(result.output_files)} files created")
    else:
        print(f"Task {i+1}: Failed - {result.error_message}")
```

### Custom Codec Settings

```python
from videolib.core.clipper import VideoClipper, ClipOptions, ClipInterval

# Create clips with H.264 re-encoding
clipper = VideoClipper()

options = ClipOptions(
    source_file="video.mp4",
    output_name="clip",
    output_extension="mp4",
    intervals=[
        ClipInterval(start_time=0, end_time=60),
        ClipInterval(start_time=120, end_time=180)
    ],
    video_codec="libx264",  # Re-encode with H.264
    audio_codec="aac"       # Re-encode audio
)

result = clipper.create_clips(options)
```

## Configuration File Format

Create a `config.json` file for batch processing:

```json
{
    "global_settings": {
        "output_extension": "mp4",
        "video_codec": "copy",
        "audio_codec": "copy"
    },
    "tasks": [
        {
            "order": 1,
            "type": "download",
            "parameters": {
                "url": "sample_video.mp4",
                "output_filename": "sample_video.mp4"
            }
        },
        {
            "order": 2,
            "type": "split",
            "parameters": {
                "source_file": "sample_video.mp4",
                "output_name": "sample_segment",
                "output_extension": "mp4",
                "max_size": "500KB"
            }
        },
        {
            "order": 3,
            "type": "clip",
            "parameters": {
                "source_file": "sample_video.mp4",
                "output_name": "sample_clip",
                "output_extension": "mp4",
                "intervals": [
                    {"start": "0", "end": "5"},
                    {"start": "5", "end": "10"}
                ]
            }
        }
    ],
    "batch_tasks":[
        {
            "type": "download",
            "task_path, ": "./videos",
            "is_parallel": true,
            "tasks":[
                {
                    "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
                    "output_filename": "sample_video_1.mp4"
                },
                {
                    "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4",
                    "output_filename": "sample_video_2.mp4"
                }
            ]
        },       
        { 
            "type": "split",
            "task_path, ": "./videos",
            "is_parallel": false,
            "tasks":[
                {
                    "source_file": "sample_video_1.mp4",
                    "output_name": "sample_segment_1",
                    "output_extension": "mp4",
                    "max_size": "500KB"
                },
                {
                    "source_file": "sample_video_2.mp4",
                    "output_name": "sample_segment_2",
                    "output_extension": "mp4",
                    "max_size": "1MB"
                }
            ]
        },
        {
            "type":"clip", 
            "task_path, ": "./videos",
            "is_parallel": false,
            "tasks":[
                {
                    "source_file": "sample_video_1.mp4",
                    "output_name": "sample_clip_1",
                    "output_extension": "mp4",
                    "intervals": [
                        {"start": "0", "end": "5"},
                        {"start": "5", "end": "10"}
                    ]
                },
                {
                    "source_file": "sample_video_2.mp4",
                    "output_name": "sample_clip_2",
                    "output_extension": "mp4",
                    "intervals": [
                        {"start": "10", "end": "15"},
                        {"start": "15", "end": "20"}
                    ]
                }
            ]
        }
    ]
}
```

## API Reference

### Core Classes

- **VideoProcessor**: Main orchestrator for all video operations
- **FFmpegWrapper**: Low-level FFmpeg/FFprobe interface
- **VideoDownloader**: Direct URL and stream downloader
- **VideoSplitter**: Split videos by file size
- **VideoClipper**: Extract time intervals from videos

### Utility Classes

- **FormatParser**: Parse size and time format strings
- **InputValidator**: Validate user inputs
- **FileManager**: File operation utilities
- **PathBuilder**: Path construction helpers

### Configuration Classes

- **ConfigurationManager**: Load and manage configurations
- **TaskTemplates**: Pre-built task configurations
- **WorkflowBuilder**: Build complex processing workflows

## Project Structure

```
videolib/
├── __init__.py              # Main package interface
├── core/                    # Core processing modules
│   └── __init__.py  
│   ├── ffmpeg_wrapper.py
│   ├── video_processor.py
│   ├── downloader.py
│   ├── splitter.py
│   ├── clipper.py
├── utils/                   # Utility modules
│   ├── __init__.py  
│   ├── file_manager.py
│   ├── format_parser.py
│   ├── path_builder.py
│   └── validators.py
├── config/                  # Configuration management
│   ├── __init__.py  
│   ├── config_manager.py
│   └── task_definitions.py
└── interfaces/              # Abstract interfaces
    ├── __init__.py  
    ├── base_interface.py
    └── task_interface.py
```

## Requirements

- Python 3.7+
- FFmpeg (external, must be installed separately)
- No Python package dependencies!

## CLI Application

For a user-friendly command-line interface, check out [videolib-cli](https://github.com/BrianAtCode/videolib-cli).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FFmpeg for powerful video processing capabilities

## Support

- 📝 [Documentation](https://github.com/BrianAtCode/videolib#readme)
- 🐛 [Issue Tracker](https://github.com/BrianAtCode/videolib/issues)
- 💬 [Discussions](https://github.com/BrianAtCode/videolib/discussions)

## Author

Kam ho, brian - [@BrianAtCode](https://github.com/BrianAtCode)

Project Link: [https://github.com/BrianAtCode/videolib](https://github.com/BrianAtCode/videolib)
