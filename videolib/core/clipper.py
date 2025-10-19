"""
Video clipper with OOP design  
"""
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from ..utils import FileManager, FormatParser, InputValidator, ValidationError
from .ffmpeg_wrapper import FFmpegWrapper, ClipCommand

@dataclass
class ClipInterval:
    """Represents a clip interval"""
    start_time: float
    end_time: float
    
    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be less than end time")
        if self.start_time < 0:
            raise ValueError("Start time cannot be negative")

@dataclass
class ClipOptions:
    """Clip operation options"""
    source_file: str
    output_name: str
    output_extension: str
    intervals: List[ClipInterval]
    video_codec: str = "copy"
    audio_codec: str = "copy"

@dataclass
class ClipResult:
    """Clip operation result"""
    success: bool
    output_files: List[str] = None
    failed_clips: List[Tuple[int, str]] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        if self.failed_clips is None:
            self.failed_clips = []

class VideoClipper:
    """Video clipper class"""
    
    def __init__(self, ffmpeg_wrapper: Optional[FFmpegWrapper] = None):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()
    
    def create_clips(self, options: ClipOptions) -> ClipResult:
        """Create video clips from intervals"""
        # Validate inputs
        try:
            self._validate_options(options)
        except ValidationError as e:
            return ClipResult(success=False, error_message=str(e))
        
        # Process each interval
        output_files = []
        failed_clips = []
        
        for i, interval in enumerate(options.intervals):
            clip_result = self._create_single_clip(options, interval, i + 1)
            
            if clip_result.success:
                output_files.extend(clip_result.output_files)
            else:
                failed_clips.append((i + 1, clip_result.error_message or "Unknown error"))
        
        # Determine overall success
        success = len(output_files) > 0
        
        return ClipResult(
            success=success,
            output_files=output_files,
            failed_clips=failed_clips
        )
    
    def _validate_options(self, options: ClipOptions) -> None:
        """Validate clip options"""
        if not FileManager.get_file_size(options.source_file):
            raise ValidationError(f"Source file not found: {options.source_file}")
        
        if not options.output_name.strip():
            raise ValidationError("Output name cannot be empty")
        
        if not options.output_extension.strip():
            raise ValidationError("Output extension cannot be empty")
        
        if not options.intervals:
            raise ValidationError("At least one interval is required")
        
        # Validate media has sufficient duration
        probe_result = self.ffmpeg.probe_media(options.source_file)
        if probe_result.success and probe_result.media_info.duration:
            duration = probe_result.media_info.duration
            
            for i, interval in enumerate(options.intervals):
                if interval.end_time > duration:
                    raise ValidationError(
                        f"Interval {i+1} end time ({interval.end_time}s) exceeds video duration ({duration}s)"
                    )
    
    def _create_single_clip(self, options: ClipOptions, interval: ClipInterval, clip_number: int) -> ClipResult:
        """Create a single clip"""
        # Generate output filename
        output_filename = f"{options.output_name}_{clip_number:03d}.{options.output_extension}"
        
        # Make filename unique if necessary
        base_name = output_filename.rsplit('.', 1)[0]
        extension = output_filename.rsplit('.', 1)[1]
        unique_base = FileManager.get_unique_filename(base_name, extension)
        output_path = f"{unique_base}.{extension}"
        
        # Execute clip command
        clip_cmd = ClipCommand(
            self.ffmpeg,
            options.source_file,
            output_path,
            interval.start_time,
            interval.end_time,
            options.video_codec,
            options.audio_codec
        )
        
        result = clip_cmd.execute()
        
        if result.success:
            return ClipResult(success=True, output_files=[output_path])
        else:
            return ClipResult(success=False, error_message=result.error_message)

# Convenience functions for backward compatibility  
def clip_video_segments(source_file: str, output_name: str, output_extension: str,
                       video_codec: str, audio_codec: str, 
                       intervals: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Create video clips - backward compatible function"""
    clipper = VideoClipper()
    
    # Convert interval tuples to ClipInterval objects
    clip_intervals = []
    for start, end in intervals:
        try:
            clip_intervals.append(ClipInterval(start_time=start, end_time=end))
        except ValueError:
            # Skip invalid intervals
            continue
    
    options = ClipOptions(
        source_file=source_file,
        output_name=output_name,
        output_extension=output_extension,
        intervals=clip_intervals,
        video_codec=video_codec,
        audio_codec=audio_codec
    )
    
    result = clipper.create_clips(options)
    
    return {
        "files": result.output_files,
        "errors": result.failed_clips,
        "out_prefix": output_name
    }
