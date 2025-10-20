"""
Video splitter with OOP design
"""
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from ..utils import FileManager, FormatParser, InputValidator, ValidationError
from .ffmpeg_wrapper import FFmpegWrapper, SegmentCommand

@dataclass
class SplitOptions:
    """Split operation options"""
    source_file: str
    output_name: str
    output_extension: str
    max_size_bytes: int
    safety_factor: float = 0.95
    max_rounds: int = 4

@dataclass 
class SplitResult:
    """Split operation result"""
    success: bool
    output_files: List[str] = None
    oversized_files: List[str] = None
    was_copied: bool = False
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        if self.oversized_files is None:
            self.oversized_files = []
    
    def __str__(self) -> str:
        """String representation for better UI display"""
        if not self.success:
            return f"Split failed: {self.error_message or 'Unknown error'}"
        
        lines = []
        if self.was_copied:
            lines.append("-> File was already smaller than target size and was copied")
        else:
            lines.append(f"-> Successfully split video into {len(self.output_files)} segment(s)")
        
        if self.output_files:
            lines.append("\n-> Output segments:")
            for i, file_path in enumerate(self.output_files, 1):
                file_size = FileManager.get_file_size(file_path)
                if file_size:
                    size_str = FormatParser.format_file_size(file_size)
                    lines.append(f"   {i}. {FileManager.get_basename(file_path)} ({size_str})")
                else:
                    lines.append(f"   {i}. {FileManager.get_basename(file_path)}")
        
        if self.oversized_files:
            lines.append(f"\n-> Warning: {len(self.oversized_files)} file(s) exceeded target size:")
            for oversized in self.oversized_files:
                file_size = FileManager.get_file_size(oversized)
                size_str = FormatParser.format_file_size(file_size) if file_size else "Unknown"
                lines.append(f"   - {FileManager.get_basename(oversized)} ({size_str})")
        
        return '\n'.join(lines)

class VideoSplitter:
    """Video splitter class"""
    
    def __init__(self, ffmpeg_wrapper: Optional[FFmpegWrapper] = None):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()
    
    def split_by_size(self, options: SplitOptions) -> SplitResult:
        """Split video by file size"""
        # Validate inputs
        try:
            self._validate_options(options)
        except ValidationError as e:
            return SplitResult(success=False, error_message=str(e))
        
        # Check if file is already small enough
        source_size = FileManager.get_file_size(options.source_file)
        if source_size <= options.max_size_bytes:
            return self._copy_file(options)
        
        # Get media info
        probe_result = self.ffmpeg.probe_media(options.source_file)
        if not probe_result.success:
            return SplitResult(success=False, error_message=probe_result.error_message)
        
        duration = probe_result.media_info.duration
        if not duration or duration <= 0:
            return SplitResult(success=False, error_message="Could not determine video duration")
        
        # Calculate segment duration
        bytes_per_sec = source_size / duration
        segment_duration = max(0.5, (options.max_size_bytes / bytes_per_sec) * options.safety_factor)
        
        # Execute segmentation
        return self._perform_segmentation(options, segment_duration)
    
    def _validate_options(self, options: SplitOptions) -> None:
        """Validate split options"""
        if not FileManager.get_file_size(options.source_file):
            raise ValidationError(f"Source file not found: {options.source_file}")
        
        if options.max_size_bytes <= 0:
            raise ValidationError("Max size must be greater than 0")
        
        if not options.output_name.strip():
            raise ValidationError("Output name cannot be empty")
        
        if not options.output_extension.strip():
            raise ValidationError("Output extension cannot be empty")
    
    def _copy_file(self, options: SplitOptions) -> SplitResult:
        """Copy file when it's already under size limit"""
        dest_path = f"{options.output_name}.{options.output_extension}"
        
        if FileManager.copy_file(options.source_file, dest_path):
            return SplitResult(
                success=True,
                output_files=[dest_path],
                was_copied=True
            )
        else:
            return SplitResult(
                success=False,
                error_message="Failed to copy file"
            )
    
    def _perform_segmentation(self, options: SplitOptions, segment_duration: float) -> SplitResult:
        """Perform FFmpeg segmentation"""
        # Build output pattern
        pattern_keyword = '%03d'
        pattern = f"{options.output_name}_{pattern_keyword}.{options.output_extension}"
        
        # Execute segment command
        segment_cmd = SegmentCommand(self.ffmpeg, options.source_file, pattern, pattern_keyword, segment_duration)
        result = segment_cmd.execute()
        
        if not result.success:
            return SplitResult(success=False, error_message=result.error_message)

        # Process segments for oversized files
        return self._process_segments(result.output_files, options)
    
    def _process_segments(self, segments: List[str], options: SplitOptions) -> SplitResult:
        """Process segments, splitting oversized ones"""
        final_files = []
        oversized_files = []
        
        for segment in segments:
            segment_size = FileManager.get_file_size(segment)
            
            if segment_size <= options.max_size_bytes:
                final_files.append(segment)
            else:
                # Try to split oversized segment
                split_files = self._split_oversized_segment(
                    segment, options.max_size_bytes, options.max_rounds
                )
                
                # Remove original oversized file
                FileManager.delete_file(segment)
                
                # Check results
                for split_file in split_files:
                    split_size = FileManager.get_file_size(split_file)
                    if split_size <= options.max_size_bytes:
                        final_files.append(split_file)
                    else:
                        oversized_files.append(split_file)
        
        # Handle single file case
        if len(final_files) == 1 and not oversized_files:
            final_name = f"{options.output_name}.{options.output_extension}"
            if FileManager.move_file(final_files[0], final_name):
                final_files = [final_name]
        
        return SplitResult(
            success=True,
            output_files=sorted(final_files),
            oversized_files=sorted(oversized_files)
        )
    
    def _split_oversized_segment(self, segment_path: str, max_size: int, max_rounds: int) -> List[str]:
        """Split an oversized segment recursively"""
        if max_rounds <= 0:
            return [segment_path]
        
        # Get segment info
        probe_result = self.ffmpeg.probe_media(segment_path)
        if not probe_result.success or not probe_result.media_info.duration:
            return [segment_path]
        
        duration = probe_result.media_info.duration
        current_size = FileManager.get_file_size(segment_path)
        
        if current_size <= max_size:
            return [segment_path]
        
        # Calculate new segment duration
        bytes_per_sec = current_size / duration
        new_duration = max(0.5, (max_size / bytes_per_sec) * 0.95)
        
        # Create unique temporary pattern
        base_name = segment_path.rsplit('.', 1)[0]
        extension = segment_path.rsplit('.', 1)[1] if '.' in segment_path else 'mp4'
        unique_id = uuid.uuid4().hex[:6]
        pattern_keyword = '%03d'
        temp_pattern = f"{base_name}_sub_{unique_id}_{pattern_keyword}.{extension}"
        
        # Execute segmentation
        segment_cmd = SegmentCommand(self.ffmpeg, segment_path, temp_pattern, pattern_keyword, new_duration)
        result = segment_cmd.execute()
        
        if not result.success:
            return [segment_path]
        
        # Recursively process new segments
        final_segments = []
        for new_segment in result.output_files:
            sub_segments = self._split_oversized_segment(new_segment, max_size, max_rounds - 1)
            final_segments.extend(sub_segments)
        
        return final_segments

# Convenience functions for backward compatibility
def split_video_by_size(source_file: str, output_name: str, output_extension: str, 
                       max_size_bytes: int, safety_factor: float = 0.95, 
                       max_rounds: int = 4) -> Dict[str, Any]:
    """Split video by size - backward compatible function"""
    splitter = VideoSplitter()
    options = SplitOptions(
        source_file=source_file,
        output_name=output_name,
        output_extension=output_extension,
        max_size_bytes=max_size_bytes,
        safety_factor=safety_factor,
        max_rounds=max_rounds
    )
    result = splitter.split_by_size(options)
    
    return {
        "files": result.output_files,
        "overs": result.oversized_files,
        "copied": result.was_copied,
        "renamed_single_to": result.output_files[0] if len(result.output_files) == 1 else None
    }