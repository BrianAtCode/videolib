"""
Validation utilities for video processing operations
"""
import os
from typing import List, Optional, Tuple, Dict, Any
from .format_utils import FormatParser

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Validate inputs for video operations"""
    
    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """Validate that file exists"""
        return os.path.isfile(file_path)
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        return FormatParser.is_valid_url(url)
    
    @staticmethod
    def validate_output_path(output_path: str) -> Tuple[bool, Optional[str]]:
        """Validate output path is writable"""
        try:
            # Check if directory exists or can be created
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Test if we can write to the location
            test_file = output_path + ".tmp"
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return True, None
            except OSError as e:
                return False, f"Cannot write to output path: {e}"
                
        except OSError as e:
            return False, f"Invalid output path: {e}"
    
    @staticmethod
    def validate_size_string(size_str: str) -> Tuple[bool, Optional[str]]:
        """Validate size string format"""
        parsed = FormatParser.parse_size(size_str)
        if parsed is None:
            return False, f"Invalid size format: '{size_str}'. Use formats like '2GB', '500MB', '1024KB'"
        
        if parsed <= 0:
            return False, "Size must be greater than 0"
        
        return True, None
    
    @staticmethod
    def validate_timecode(timecode: str) -> Tuple[bool, Optional[str]]:
        """Validate timecode format"""
        parsed = FormatParser.parse_timecode(timecode)
        if parsed is None:
            return False, f"Invalid timecode format: '{timecode}'. Use formats like 'HH:MM:SS', 'MM:SS', or seconds"
        
        if parsed < 0:
            return False, "Timecode cannot be negative"
        
        return True, None
    
    @staticmethod
    def validate_time_intervals(intervals: List[Tuple[str, str]]) -> Tuple[bool, List[str]]:
        """Validate list of time intervals"""
        errors = []
        
        for i, (start, end) in enumerate(intervals):
            # Validate individual timecodes
            start_valid, start_error = InputValidator.validate_timecode(start)
            if not start_valid:
                errors.append(f"Interval {i+1} start time: {start_error}")
            
            end_valid, end_error = InputValidator.validate_timecode(end)
            if not end_valid:
                errors.append(f"Interval {i+1} end time: {end_error}")
            
            # Check start < end
            if start_valid and end_valid:
                start_sec = FormatParser.parse_timecode(start)
                end_sec = FormatParser.parse_timecode(end)
                
                if start_sec >= end_sec:
                    errors.append(f"Interval {i+1}: start time must be less than end time")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_codec(codec: str) -> Tuple[bool, Optional[str]]:
        """Validate codec name"""
        if not codec or not codec.strip():
            return False, "Codec cannot be empty"
        
        # Basic validation - allow common codecs
        valid_codecs = {
            'copy', 'libx264', 'libx265', 'h264', 'h265', 'vp8', 'vp9', 'av1',
            'aac', 'mp3', 'opus', 'vorbis', 'flac', 'pcm'
        }
        
        if codec.lower() not in valid_codecs and not codec.startswith('lib'):
            # Warning but not error - allow unknown codecs
            pass
        
        return True, None

class ConfigValidator:
    """Validate configuration objects"""
    
    @staticmethod
    def validate_download_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate download configuration"""
        errors = []
        
        # Required fields
        if 'url' not in config:
            errors.append("Missing required field: 'url'")
        elif not InputValidator.validate_url(config['url']):
            errors.append(f"Invalid URL: '{config['url']}'")
        
        if 'output_filename' not in config:
            errors.append("Missing required field: 'output_filename'")
        elif not config['output_filename'].strip():
            errors.append("Output filename cannot be empty")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_split_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate split configuration"""
        errors = []
        
        # Required fields
        required_fields = ['source_file', 'output_name', 'output_extension', 'max_size']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: '{field}'")
            elif not str(config[field]).strip():
                errors.append(f"Field '{field}' cannot be empty")
        
        # Validate source file exists
        if 'source_file' in config and not InputValidator.validate_file_exists(config['source_file']):
            errors.append(f"Source file does not exist: '{config['source_file']}'")
        
        # Validate size format
        if 'max_size' in config:
            size_valid, size_error = InputValidator.validate_size_string(config['max_size'])
            if not size_valid:
                errors.append(size_error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_clip_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate clip configuration"""
        errors = []
        
        # Required fields
        required_fields = ['source_file', 'output_name', 'output_extension', 'intervals']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate source file exists
        if 'source_file' in config and not InputValidator.validate_file_exists(config['source_file']):
            errors.append(f"Source file does not exist: '{config['source_file']}'")
        
        # Validate intervals
        if 'intervals' in config:
            if not isinstance(config['intervals'], list):
                errors.append("'intervals' must be a list")
            elif len(config['intervals']) == 0:
                errors.append("'intervals' list cannot be empty")
            else:
                # Convert intervals to string tuples for validation
                interval_tuples = []
                for i, interval in enumerate(config['intervals']):
                    if not isinstance(interval, dict):
                        errors.append(f"Interval {i+1} must be a dictionary")
                        continue
                    
                    if 'start' not in interval or 'end' not in interval:
                        errors.append(f"Interval {i+1} must have 'start' and 'end' fields")
                        continue
                    
                    interval_tuples.append((str(interval['start']), str(interval['end'])))
                
                if interval_tuples:
                    intervals_valid, interval_errors = InputValidator.validate_time_intervals(interval_tuples)
                    errors.extend(interval_errors)
        
        # Validate codecs if present
        for codec_field in ['video_codec', 'audio_codec']:
            if codec_field in config:
                codec_valid, codec_error = InputValidator.validate_codec(config[codec_field])
                if not codec_valid:
                    errors.append(f"{codec_field}: {codec_error}")
        
        return len(errors) == 0, errors
