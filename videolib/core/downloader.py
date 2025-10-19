"""
Video downloader with OOP design
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..utils import FileManager, FormatParser, InputValidator, ValidationError
from .ffmpeg_wrapper import FFmpegWrapper, DownloadCommand, FFmpegResult

@dataclass  
class DownloadOptions:
    """Download operation options"""
    url: str
    output_path: str
    overwrite: bool = True

@dataclass
class DownloadResult:
    """Download operation result"""
    success: bool
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None

class VideoDownloader:
    """Video downloader class"""
    
    def __init__(self, ffmpeg_wrapper: Optional[FFmpegWrapper] = None):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()
    
    def download(self, options: DownloadOptions) -> DownloadResult:
        """Download video from URL"""
        # Validate inputs
        try:
            self._validate_options(options)
        except ValidationError as e:
            return DownloadResult(success=False, error_message=str(e))
        
        # Prepare output path
        output_path = self._prepare_output_path(options)
        
        # Execute download command
        download_cmd = DownloadCommand(self.ffmpeg, options.url, output_path)
        result = download_cmd.execute()
        
        if result.success:
            # Get file size
            file_size = FileManager.get_file_size(output_path)
            return DownloadResult(
                success=True,
                output_file=output_path,
                file_size=file_size
            )
        else:
            return DownloadResult(
                success=False,
                error_message=result.error_message
            )
    
    def _validate_options(self, options: DownloadOptions) -> None:
        """Validate download options"""
        if not InputValidator.validate_url(options.url):
            raise ValidationError(f"Invalid URL: {options.url}")
        
        if not options.output_path or not options.output_path.strip():
            raise ValidationError("Output path cannot be empty")
    
    def _prepare_output_path(self, options: DownloadOptions) -> str:
        """Prepare output path, ensuring uniqueness if needed"""
        output_path = options.output_path
        
        # If file exists and overwrite is False, make unique
        if not options.overwrite and FileManager.get_file_size(output_path) is not None:
            base_name = output_path.rsplit('.', 1)[0] if '.' in output_path else output_path
            extension = output_path.rsplit('.', 1)[1] if '.' in output_path else ''
            
            output_path = FileManager.get_unique_filename(base_name, extension)
            if extension:
                output_path += '.' + extension
        
        return output_path

# Convenience functions for backward compatibility
def download_video(url: str, output_filename: str) -> Dict[str, Any]:
    """Download video - backward compatible function"""
    downloader = VideoDownloader()
    options = DownloadOptions(url=url, output_path=output_filename)
    result = downloader.download(options)
    
    return {
        "success": result.success,
        "error": result.error_message,
        "output": result.output_file or output_filename
    }
