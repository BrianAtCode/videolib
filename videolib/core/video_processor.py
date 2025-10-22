"""
Main video processor that orchestrates all operations
"""

from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass

from .ffmpeg_wrapper import FFmpegWrapper, MediaInfo
from .downloader import VideoDownloader, DownloadOptions, DownloadResult
from .splitter import VideoSplitter, SplitOptions, SplitResult
from .clipper import VideoClipper, ClipOptions, ClipResult, ClipInterval
from .gif_converter import VideoGifConverter, AutoGifOptions
from ..interfaces.gif_interface import GifOptions, GifResult, GifInterval
from ..utils import FormatParser, InputValidator, ValidationError


@dataclass
class ProcessorConfig:
    """Configuration for video processor"""
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    default_video_codec: str = "copy"
    default_audio_codec: str = "copy"
    default_output_extension: str = "mp4"


class VideoProcessor:
    """Main video processor class - high level interface"""

    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()
        self.ffmpeg = FFmpegWrapper(self.config.ffmpeg_path, self.config.ffprobe_path)

        # Initialize processors
        self.downloader = VideoDownloader(self.ffmpeg)
        self.splitter = VideoSplitter(self.ffmpeg)
        self.clipper = VideoClipper(self.ffmpeg)
        self.gif_converter = VideoGifConverter(self.ffmpeg)

    def get_media_info(self, file_path: str) -> Optional[MediaInfo]:
        """Get media information for a file"""
        result = self.ffmpeg.probe_media(file_path)
        return result.media_info if result.success else None

    def download_video(self, url: str, output_path: str, overwrite: bool = True) -> DownloadResult:
        """Download video from URL"""
        options = DownloadOptions(
            url=url,
            output_path=output_path,
            overwrite=overwrite
        )

        return self.downloader.download(options)

    def split_video_by_size(self, source_file: str, output_name: str,
                           max_size: Union[str, int], output_extension: Optional[str] = None,
                           safety_factor: float = 0.95, max_rounds: int = 4) -> SplitResult:
        """Split video by file size"""
        # Parse size if string
        if isinstance(max_size, str):
            max_size_bytes = FormatParser.parse_size(max_size)
            if max_size_bytes is None:
                raise ValidationError(f"Invalid size format: {max_size}")
        else:
            max_size_bytes = int(max_size)

        # Use default extension if not provided
        if output_extension is None:
            output_extension = self.config.default_output_extension

        options = SplitOptions(
            source_file=source_file,
            output_name=output_name,
            output_extension=output_extension,
            max_size_bytes=max_size_bytes,
            safety_factor=safety_factor,
            max_rounds=max_rounds
        )

        return self.splitter.split_by_size(options)

    def create_clips(self, source_file: str, output_name: str, intervals: List[Dict[str, Any]],
                    output_extension: Optional[str] = None, video_codec: Optional[str] = None,
                    audio_codec: Optional[str] = None) -> ClipResult:
        """Create video clips from time intervals"""
        # Parse intervals
        clip_intervals = []
        for i, interval in enumerate(intervals):
            try:
                start = FormatParser.parse_timecode(interval.get('start'))
                end = FormatParser.parse_timecode(interval.get('end'))

                if start is None or end is None:
                    raise ValidationError(f"Invalid timecode in interval {i+1}")

                clip_intervals.append(ClipInterval(start_time=start, end_time=end))

            except (ValueError, ValidationError) as e:
                raise ValidationError(f"Interval {i+1}: {e}")

        # Use defaults if not provided
        if output_extension is None:
            output_extension = self.config.default_output_extension
        if video_codec is None:
            video_codec = self.config.default_video_codec
        if audio_codec is None:
            audio_codec = self.config.default_audio_codec

        options = ClipOptions(
            source_file=source_file,
            output_name=output_name,
            output_extension=output_extension,
            intervals=clip_intervals,
            video_codec=video_codec,
            audio_codec=audio_codec
        )

        return self.clipper.create_clips(options)

    def create_gif_clips(self, source_file: str, intervals: List[Tuple[float, float]],
                        output_name: str, **kwargs) -> GifResult:
        """Create GIF clips from video intervals"""
        return self.gif_converter.create_gif_from_intervals(
            source_file, intervals, output_name, **kwargs
        )

    def create_auto_gif_clips(self, source_file: str, num_clips: int, 
                             gif_duration: float, time_gap: float, 
                             output_name: str, **kwargs) -> GifResult:
        """Create auto-generated GIF clips with time gaps and enhanced features"""
        options = AutoGifOptions(
            source_file=source_file,
            num_clips=num_clips,
            gif_duration=gif_duration,
            time_gap=time_gap,
            output_name=output_name,
            **kwargs
        )
        
        return self.gif_converter.create_auto_generated_clips(options)

    def process_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple tasks in sequence"""
        results = []
        for i, task in enumerate(tasks):
            task_type = task.get('type')
            task_params = task.get('parameters', {})

            try:
                if task_type == 'download':
                    result = self.download_video(**task_params)
                elif task_type == 'split':
                    result = self.split_video_by_size(**task_params)
                elif task_type == 'clip':
                    result = self.create_clips(**task_params)
                elif task_type == 'gif':
                    # Support both old and new GIF creation methods
                    if 'gif_duration' in task_params and 'time_gap' in task_params:
                        result = self.create_auto_gif_clips(**task_params)
                    else:
                        result = self.create_gif_clips(**task_params)
                else:
                    result = {'success': False, 'error_message': f'Unknown task type: {task_type}'}

                results.append({
                    'task_index': i,
                    'task_type': task_type,
                    'result': result
                })

            except Exception as e:
                results.append({
                    'task_index': i,
                    'task_type': task_type,
                    'result': {'success': False, 'error_message': str(e)}
                })

        # Calculate summary
        successful = sum(1 for r in results if getattr(r['result'], 'success', r['result'].get('success', False)))

        return {
            'results': results,
            'total_tasks': len(tasks),
            'successful_tasks': successful,
            'failed_tasks': len(tasks) - successful,
            'success_rate': (successful / len(tasks)) * 100 if tasks else 0
        }


# Factory function for easy instantiation
def create_video_processor(ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe") -> VideoProcessor:
    """Create a video processor with custom FFmpeg paths"""
    config = ProcessorConfig(ffmpeg_path=ffmpeg_path, ffprobe_path=ffprobe_path)
    return VideoProcessor(config)
