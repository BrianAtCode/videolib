"""
Video processing core modules
"""
from .ffmpeg_wrapper import FFmpegWrapper, MediaInfo, FFmpegResult
from .video_processor import VideoProcessor, ProcessorConfig, create_video_processor
from .downloader import VideoDownloader, DownloadOptions, DownloadResult
from .splitter import VideoSplitter, SplitOptions, SplitResult
from .clipper import VideoClipper, ClipOptions, ClipResult, ClipInterval

# Backward compatibility functions
from .downloader import download_video
from .splitter import split_video_by_size
from .clipper import clip_video_segments

__all__ = [
    # Main classes
    'VideoProcessor',
    'ProcessorConfig',
    'create_video_processor',
    
    # Core components
    'FFmpegWrapper',
    'VideoDownloader',
    'VideoSplitter', 
    'VideoClipper',
    
    # Data structures
    'MediaInfo',
    'FFmpegResult',
    'DownloadOptions',
    'DownloadResult',
    'SplitOptions',
    'SplitResult',
    'ClipOptions',
    'ClipResult',
    'ClipInterval',
    
    # Backward compatibility
    'download_video',
    'split_video_by_size',
    'clip_video_segments'
]
