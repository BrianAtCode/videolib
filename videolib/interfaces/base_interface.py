"""
Base interfaces for video processing operations
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class VideoOperation(ABC):
    """Abstract base class for video operations"""
    
    @abstractmethod
    def execute(self) -> Any:
        """Execute the operation"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate operation parameters"""
        pass

class ResultHandler(ABC):
    """Abstract base class for result handlers"""
    
    @abstractmethod
    def handle_success(self, result: Any) -> None:
        """Handle successful operation result"""
        pass
    
    @abstractmethod
    def handle_failure(self, error: str) -> None:
        """Handle failed operation result"""
        pass

class ProgressReporter(ABC):
    """Abstract base class for progress reporting"""
    
    @abstractmethod
    def report_start(self, operation: str, total_steps: int) -> None:
        """Report operation start"""
        pass
    
    @abstractmethod
    def report_progress(self, step: int, message: str) -> None:
        """Report progress update"""
        pass
    
    @abstractmethod
    def report_complete(self, success: bool, message: str) -> None:
        """Report operation completion"""
        pass

class ConfigProvider(ABC):
    """Abstract base class for configuration providers"""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value"""
        pass
