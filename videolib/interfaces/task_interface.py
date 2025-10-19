"""
Task-specific interfaces for video processing
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .base_interface import VideoOperation, ResultHandler, ProgressReporter

class DownloadOperation(VideoOperation):
    """Download operation interface"""
    
    def __init__(self, url: str, output_path: str):
        self.url = url
        self.output_path = output_path
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute download operation"""
        pass
    
    def validate(self) -> bool:
        """Validate download parameters"""
        return bool(self.url and self.output_path)

class SplitOperation(VideoOperation):
    """Split operation interface"""
    
    def __init__(self, source_file: str, output_name: str, max_size: int):
        self.source_file = source_file
        self.output_name = output_name
        self.max_size = max_size
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute split operation"""
        pass
    
    def validate(self) -> bool:
        """Validate split parameters"""
        return bool(self.source_file and self.output_name and self.max_size > 0)

class ClipOperation(VideoOperation):
    """Clip operation interface"""
    
    def __init__(self, source_file: str, output_name: str, intervals: List[Dict[str, Any]]):
        self.source_file = source_file
        self.output_name = output_name
        self.intervals = intervals
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute clip operation"""
        pass
    
    def validate(self) -> bool:
        """Validate clip parameters"""
        return bool(self.source_file and self.output_name and self.intervals)

class BatchProcessor(ABC):
    """Interface for batch processing multiple operations"""
    
    @abstractmethod
    def add_operation(self, operation: VideoOperation) -> None:
        """Add operation to batch"""
        pass
    
    @abstractmethod
    def execute_batch(self, progress_reporter: Optional[ProgressReporter] = None) -> Dict[str, Any]:
        """Execute all operations in batch"""
        pass
    
    @abstractmethod
    def clear_batch(self) -> None:
        """Clear all operations from batch"""
        pass

class TaskFactory(ABC):
    """Factory interface for creating video operations"""
    
    @abstractmethod
    def create_download_task(self, params: Dict[str, Any]) -> DownloadOperation:
        """Create download operation"""
        pass
    
    @abstractmethod
    def create_split_task(self, params: Dict[str, Any]) -> SplitOperation:
        """Create split operation"""  
        pass
    
    @abstractmethod
    def create_clip_task(self, params: Dict[str, Any]) -> ClipOperation:
        """Create clip operation"""
        pass
