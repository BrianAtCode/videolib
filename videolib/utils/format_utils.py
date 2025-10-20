"""
Format and parsing utilities for video processing
"""
import os
import re
from typing import Optional, Union

class FormatParser:
    """Parse various format strings"""
    
    @staticmethod
    def parse_size(size_str: str) -> Optional[int]:
        """Parse size string (e.g., '2GB', '500MB') to bytes"""
        if not size_str:
            return None
        
        size_str = size_str.strip().upper().replace(' ', '')
        
        try:
            # Plain number (bytes)
            if size_str.isdigit():
                return int(size_str)
            
            # Parse with units
            match = re.match(r'^([0-9]*\.?[0-9]+)(GB?|MB?|KB?|B?)$', size_str)
            if not match:
                return None
            
            value = float(match.group(1))
            unit = match.group(2)
            
            multipliers = {
                'B': 1,
                'KB': 1024,
                'K': 1024,
                'MB': 1024 ** 2,
                'M': 1024 ** 2,
                'GB': 1024 ** 3,
                'G': 1024 ** 3
            }
            
            return int(value * multipliers.get(unit, 1))
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def parse_timecode(timecode: Union[str, int, float]) -> Optional[float]:
        """Parse timecode to seconds (supports HH:MM:SS, MM:SS, or seconds)"""
        if timecode is None:
            return None
        
        # Convert to string for processing
        if isinstance(timecode, (int, float)):
            return float(timecode)
        
        timecode_str = str(timecode).strip()
        if not timecode_str:
            return None
        
        try:
            # Plain seconds
            if ':' not in timecode_str:
                return float(timecode_str)
            
            # HH:MM:SS or MM:SS format
            parts = [float(p) for p in timecode_str.split(':') if p.strip()]
            
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = parts
            elif len(parts) == 2:  # MM:SS
                hours = 0
                minutes, seconds = parts
            elif len(parts) == 1:  # SS
                hours = minutes = 0
                seconds = parts[0]
            else:
                return None
            
            return hours * 3600 + minutes * 60 + seconds
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        if seconds < 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format bytes as human readable string"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is a valid URL"""
        if not url:
            return False
        return url.startswith(('http://', 'https://'))
    
    @staticmethod
    def normalize_extension(extension: str) -> str:
        """Normalize file extension (remove dot, lowercase)"""
        if not extension:
            return ""
        
        ext = extension.strip()
        if ext.startswith('.'):
            ext = ext[1:]
        
        return ext.lower()

class PathBuilder:
    """Build file paths for video operations"""
    
    @staticmethod
    def build_output_path(base_name: str, extension: str, suffix: str = "", 
                         directory: str = "") -> str:
        """Build output file path"""
        if not extension.startswith('.'):
            extension = '.' + extension
        
        filename = base_name + suffix + extension
        
        if directory:
            return os.path.join(directory, filename)
        
        return filename
    
    @staticmethod
    def build_segment_pattern(base_name: str, extension: str, 
                            directory: str = "") -> str:
        """Build FFmpeg segment output pattern"""
        if not extension.startswith('.'):
            extension = '.' + extension
        
        pattern = base_name + "_%03d" + extension
        
        if directory:
            return os.path.join(directory, pattern)
        
        return pattern
