"""
FFmpeg wrapper module - provides OOP interface to FFmpeg operations
"""
import glob
import os
import json
import subprocess
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class MediaInfo:
    """Media information data structure"""
    duration: Optional[float] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    format_name: Optional[str] = None
    size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None

@dataclass
class FFmpegResult:
    """Result of FFmpeg operation"""
    success: bool
    error_message: Optional[str] = None
    output_files: List[str] = None
    media_info: Optional[MediaInfo] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []

class FFmpegCommand(ABC):
    """Abstract base class for FFmpeg commands"""
    
    @abstractmethod
    def build_command(self) -> List[str]:
        """Build the FFmpeg command as list of strings"""
        pass
    
    @abstractmethod
    def execute(self) -> FFmpegResult:
        """Execute the command and return result"""
        pass

class FFmpegWrapper:
    """Main FFmpeg wrapper class"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._validate_executables()
    
    def _validate_executables(self) -> None:
        """Validate FFmpeg and FFprobe are available"""
        for exe in [self.ffmpeg_path, self.ffprobe_path]:
            try:
                subprocess.run([exe, "-version"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError(f"{exe} executable not found or not working")
    
    def probe_media(self, file_path: str) -> FFmpegResult:
        """Probe media file for information"""
        if not os.path.exists(file_path):
            return FFmpegResult(success=False, error_message=f"File not found: {file_path}")
        
        cmd = [
            self.ffprobe_path, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", file_path
        ]
        
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                text=True, check=True)
            data = json.loads(proc.stdout)
            
            # Parse media information
            media_info = self._parse_media_info(data, file_path)
            
            return FFmpegResult(success=True, media_info=media_info)
            
        except subprocess.CalledProcessError as e:
            return FFmpegResult(success=False, error_message=f"FFprobe failed: {e.stderr}")
        except json.JSONDecodeError as e:
            return FFmpegResult(success=False, error_message=f"JSON decode error: {e}")
        except Exception as e:
            return FFmpegResult(success=False, error_message=str(e))
    
    def _parse_media_info(self, data: Dict[str, Any], file_path: str) -> MediaInfo:
        """Parse FFprobe JSON data into MediaInfo"""
        fmt = data.get("format", {})
        streams = data.get("streams", [])
        
        # Parse duration
        duration = None
        try:
            duration = float(fmt.get("duration", 0)) if fmt.get("duration") else None
        except (ValueError, TypeError):
            pass
        
        # Parse codecs and stream info
        video_codec = None
        audio_codec = None
        width = None
        height = None
        
        for stream in streams:
            if stream.get("codec_type") == "video" and not video_codec:
                video_codec = stream.get("codec_name")
                width = stream.get("width")
                height = stream.get("height")
            elif stream.get("codec_type") == "audio" and not audio_codec:
                audio_codec = stream.get("codec_name")
        
        # Get file size
        size_bytes = None
        try:
            size_bytes = os.path.getsize(file_path)
        except OSError:
            pass
        
        # Parse bitrate
        bitrate = None
        try:
            bitrate = int(fmt.get("bit_rate", 0)) if fmt.get("bit_rate") else None
        except (ValueError, TypeError):
            pass
        
        return MediaInfo(
            duration=duration,
            video_codec=video_codec,
            audio_codec=audio_codec,
            format_name=fmt.get("format_name"),
            size_bytes=size_bytes,
            width=width,
            height=height,
            bitrate=bitrate
        )
    
    def get_duration_seconds(self, file_path: str) -> Optional[float]:
        """Get duration in seconds (convenience method)"""
        result = self.probe_media(file_path)
        if result.success and result.media_info:
            return result.media_info.duration
        return None

class DownloadCommand(FFmpegCommand):
    """FFmpeg download command"""
    
    def __init__(self, wrapper: FFmpegWrapper, url: str, output_path: str):
        self.wrapper = wrapper
        self.url = url
        self.output_path = output_path
    
    def build_command(self) -> List[str]:
        """Build download command"""
        return [
            self.wrapper.ffmpeg_path,
            "-y",  # overwrite without asking
            "-i", self.url,
            "-c", "copy",  # stream copy
            self.output_path
        ]
    
    def execute(self) -> FFmpegResult:
        """Execute download command"""
        # Ensure output directory exists
        out_dir = os.path.dirname(self.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        cmd = self.build_command()
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            
            # Verify output file exists
            if os.path.exists(self.output_path):
                return FFmpegResult(success=True, output_files=[self.output_path])
            else:
                return FFmpegResult(success=False, error_message="Output file was not created")
                
        except subprocess.CalledProcessError as e:
            return FFmpegResult(success=False, error_message=f"FFmpeg failed: {e.stderr}")
        except Exception as e:
            return FFmpegResult(success=False, error_message=str(e))

class SegmentCommand(FFmpegCommand):
    """FFmpeg segment command"""
    
    def __init__(self, wrapper: FFmpegWrapper, input_path: str, output_pattern: str, pattern_keyword: str, segment_duration: float):
        self.wrapper = wrapper
        self.input_path = input_path
        self.output_pattern = output_pattern
        self.pattern_keyword = pattern_keyword
        self.segment_duration = segment_duration
    
    def build_command(self) -> List[str]:
        """Build segment command"""
        return [
            self.wrapper.ffmpeg_path,
            "-y",
            "-i", self.input_path,
            "-c", "copy",
            "-map", "0",
            "-f", "segment",
            "-segment_time", f"{self.segment_duration:.3f}",
            "-reset_timestamps", "1",
            self.output_pattern
        ]
    
    def execute(self) -> FFmpegResult:
        """Execute segment command"""
        # Ensure output directory exists
        out_dir = os.path.dirname(self.output_pattern)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        cmd = self.build_command()
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            
            # Find created segments
            output_dir = os.path.dirname(self.output_pattern) or "."
            glob_pattern = self.output_pattern.replace(self.pattern_keyword, '*')

            segments = []
            try:
                segments = glob.glob(glob_pattern)
                segments = [os.path.join(output_dir, os.path.basename(f)) for f in segments]
                segments.sort()
            except OSError:
                pass
            
            return FFmpegResult(success=True, output_files=segments)
            
        except subprocess.CalledProcessError as e:
            return FFmpegResult(success=False, error_message=f"FFmpeg segmentation failed: {e.stderr}")
        except Exception as e:
            return FFmpegResult(success=False, error_message=str(e))

class ClipCommand(FFmpegCommand):
    """FFmpeg clip command"""
    
    def __init__(self, wrapper: FFmpegWrapper, input_path: str, output_path: str, 
                 start_time: float, end_time: float, video_codec: str = "copy", audio_codec: str = "copy"):
        self.wrapper = wrapper
        self.input_path = input_path
        self.output_path = output_path
        self.start_time = start_time
        self.end_time = end_time
        self.video_codec = video_codec
        self.audio_codec = audio_codec
    
    def build_command(self) -> List[str]:
        """Build clip command"""
        return [
            self.wrapper.ffmpeg_path,
            "-y",
            "-ss", f"{self.start_time:.3f}",
            "-to", f"{self.end_time:.3f}",
            "-i", self.input_path,
            "-c:v", self.video_codec,
            "-c:a", self.audio_codec,
            self.output_path
        ]
    
    def execute(self) -> FFmpegResult:
        """Execute clip command"""
        # Ensure output directory exists
        out_dir = os.path.dirname(self.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        cmd = self.build_command()
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            
            # Verify output file exists
            if os.path.exists(self.output_path):
                return FFmpegResult(success=True, output_files=[self.output_path])
            else:
                return FFmpegResult(success=False, error_message="Output file was not created")
                
        except subprocess.CalledProcessError as e:
            return FFmpegResult(success=False, error_message=f"FFmpeg clip failed: {e.stderr}")
        except Exception as e:
            return FFmpegResult(success=False, error_message=str(e))
