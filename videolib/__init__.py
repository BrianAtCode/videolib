"""
VideoLib - Professional Video Processing Library

A comprehensive library for video downloading, splitting, and clipping operations
with support for batch processing and flexible configuration management.
"""

# Main classes
from .core import (
    VideoProcessor, ProcessorConfig, create_video_processor,
    FFmpegWrapper, MediaInfo
)

# Configuration management
from .config import (
    ConfigurationManager, ProcessingConfig, TaskConfig,
    load_config_from_file, TaskTemplates, WorkflowBuilder
)

# Utilities
from .utils import (
    FileManager, FormatParser, PathBuilder,
    InputValidator, ConfigValidator, ValidationError
)

# Version info
__version__ = "1.0.0"
__author__ = "Video Processing Team"
__description__ = "Professional video processing library with FFmpeg integration"

# Convenience imports for backward compatibility
from .core import download_video, split_video_by_size, clip_video_segments

# Main API classes for easy access
__all__ = [
    # Core API
    'VideoProcessor',
    'ProcessorConfig', 
    'create_video_processor',
    
    # Configuration
    'ConfigurationManager',
    'ProcessingConfig',
    'TaskConfig',
    'load_config_from_file',
    'TaskTemplates',
    'WorkflowBuilder',
    
    # Utilities
    'FileManager',
    'FormatParser',
    'PathBuilder',
    'InputValidator',
    'ConfigValidator',
    'ValidationError',
    
    # Media info
    'FFmpegWrapper',
    'MediaInfo',
    
    # Backward compatibility
    'download_video',
    'split_video_by_size', 
    'clip_video_segments',
    
    # Version
    '__version__'
]

def get_version() -> str:
    """Get library version"""
    return __version__

def create_processor(**kwargs) -> VideoProcessor:
    """Create video processor with optional configuration
    
    Args:
        **kwargs: Configuration options (ffmpeg_path, ffprobe_path, etc.)
    
    Returns:
        VideoProcessor: Configured processor instance
    """
    return create_video_processor(**kwargs)

# Quick start functions
def quick_download(url: str, output_path: str) -> dict:
    """Quick download function
    
    Args:
        url: Video URL to download
        output_path: Output file path
        
    Returns:
        dict: Result with success/error information
    """
    processor = create_processor()
    result = processor.download_video(url, output_path)
    return {
        "success": result.success,
        "output_file": result.output_file,
        "error": result.error_message,
        "file_size": result.file_size
    }

def quick_split(source_file: str, output_name: str, max_size: str) -> dict:
    """Quick split function
    
    Args:
        source_file: Source video file
        output_name: Output name prefix
        max_size: Maximum size per segment (e.g., "2GB", "500MB")
        
    Returns:
        dict: Result with success/error information and output files
    """
    processor = create_processor()
    result = processor.split_video_by_size(source_file, output_name, max_size)
    return {
        "success": result.success,
        "output_files": result.output_files,
        "oversized_files": result.oversized_files,
        "error": result.error_message
    }

def quick_clip(source_file: str, output_name: str, intervals: list) -> dict:
    """Quick clip function
    
    Args:
        source_file: Source video file
        output_name: Output name prefix  
        intervals: List of intervals with start/end times
        
    Returns:
        dict: Result with success/error information and output files
    """
    processor = create_processor()
    result = processor.create_clips(source_file, output_name, intervals)
    return {
        "success": result.success,
        "output_files": result.output_files,
        "failed_clips": result.failed_clips,
        "error": result.error_message
    }
