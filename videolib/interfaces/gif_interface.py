from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

@dataclass
class GifInterval:
    """Represents a time interval for GIF creation"""
    start_time: float
    end_time: float
    output_name: str

@dataclass
class GifOptions:
    """Configuration options for GIF creation"""
    source_file: str
    intervals: List[GifInterval]
    output_extension: str = "gif"
    fps: int = 10
    scale_width: int = 320
    quality_level: str = "medium"  # low, medium, high
    loop_count: int = 0  # 0 = infinite loop
    create_thumbnails: bool = True
    thumbnail_extension: str = "png"

@dataclass
class GifResult:
    """Result of GIF conversion operation"""
    success: bool
    gif_files: List[str]
    thumbnail_files: List[str]
    total_duration: float
    error_message: Optional[str] = None
    processing_time: float = 0.0
    media_info: Optional[Dict[str, str]] = None  # Added for metadata

@dataclass
class AutoGifOptions:
    """Options for auto-generated GIF clips with time gaps"""
    source_file: str
    num_clips: int
    gif_duration: float  # Duration of each GIF clip
    time_gap: float  # Gap between clip start times
    output_name: str = "auto_clip"
    fps: int = 10
    scale_width: int = 320
    quality_level: str = "medium"
    create_thumbnails: bool = True
    create_grid: bool = True
    merge_gifs: bool = True
    grid_size: int = 5
    cleanup_individual_thumbs: bool = False
    final_gif_width: int = 640 
    final_gif_height: int = 0  
    grid_thumb_width: int = 160    
    grid_thumb_height: int = 90    
    grid_max_width: int = 1920 
    grid_max_height: int = 1080

class GifConverterInterface(ABC):
    """Abstract interface for GIF conversion operations"""
    
    @abstractmethod
    def create_gifs(self, options: GifOptions) -> GifResult:
        """Create multiple GIF clips from video"""
        pass
    
    @abstractmethod
    def create_gif_from_intervals(self, source_file: str, intervals: List[Tuple[float, float]], 
                                output_name: str, **kwargs) -> GifResult:
        """Simplified method for creating GIFs with intervals"""
        pass
    
    @abstractmethod
    def create_auto_generated_clips(self, options: AutoGifOptions) -> GifResult:
        """Create auto-generated GIF clips with time gaps and merging"""
        pass
