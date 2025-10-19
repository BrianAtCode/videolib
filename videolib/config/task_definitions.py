"""
Task definitions and templates for common video processing operations
"""
from typing import Dict, Any, List
from .config_manager import TaskConfig, ProcessingConfig, ConfigurationManager

class TaskTemplates:
    """Pre-defined task templates for common operations"""
    
    @staticmethod
    def youtube_download_and_split(url: str, output_name: str, max_size: str = "2GB") -> ProcessingConfig:
        """Template: Download from URL and split by size"""
        manager = ConfigurationManager()
        
        tasks = [
            manager.create_download_task(url, f"{output_name}_raw.mp4"),
            manager.create_split_task(
                source_file=f"{output_name}_raw.mp4",
                output_name=f"{output_name}_part",
                output_extension="mp4",
                max_size=max_size
            )
        ]
        
        global_settings = {
            "output_extension": "mp4",
            "video_codec": "copy",
            "audio_codec": "copy"
        }
        
        return manager.create_config(tasks, global_settings)
    
    @staticmethod
    def lecture_segmentation(source_file: str, chapter_intervals: List[Dict[str, Any]]) -> ProcessingConfig:
        """Template: Split lecture/presentation into chapters"""
        manager = ConfigurationManager()
        
        # Create base name from source file
        base_name = source_file.rsplit('.', 1)[0] if '.' in source_file else source_file
        
        tasks = [
            manager.create_clip_task(
                source_file=source_file,
                output_name=f"{base_name}_chapter",
                output_extension="mp4",
                intervals=chapter_intervals,
                video_codec="libx264",  # Re-encode for compatibility
                audio_codec="aac"
            )
        ]
        
        global_settings = {
            "video_codec": "libx264",
            "audio_codec": "aac",
            "output_extension": "mp4"
        }
        
        return manager.create_config(tasks, global_settings)
    
    @staticmethod
    def highlight_extraction(source_file: str, highlight_intervals: List[Dict[str, Any]]) -> ProcessingConfig:
        """Template: Extract highlights from video"""
        manager = ConfigurationManager()
        
        base_name = source_file.rsplit('.', 1)[0] if '.' in source_file else source_file
        
        tasks = [
            manager.create_clip_task(
                source_file=source_file,
                output_name=f"{base_name}_highlight",
                output_extension="mp4",
                intervals=highlight_intervals,
                video_codec="copy",  # Stream copy for speed
                audio_codec="copy"
            )
        ]
        
        return manager.create_config(tasks)
    
    @staticmethod
    def batch_processing(source_files: List[str], operation_type: str, **kwargs) -> ProcessingConfig:
        """Template: Batch process multiple files"""
        manager = ConfigurationManager()
        tasks = []
        
        for i, source_file in enumerate(source_files):
            base_name = source_file.rsplit('.', 1)[0] if '.' in source_file else source_file
            
            if operation_type == "split":
                max_size = kwargs.get("max_size", "1GB")
                output_name = kwargs.get("output_name", f"{base_name}_split")
                
                task = manager.create_split_task(
                    source_file=source_file,
                    output_name=output_name,
                    output_extension="mp4",
                    max_size=max_size
                )
                
            elif operation_type == "clip":
                intervals = kwargs.get("intervals", [{"start": "0", "end": "60"}])
                output_name = kwargs.get("output_name", f"{base_name}_clip")
                
                task = manager.create_clip_task(
                    source_file=source_file,
                    output_name=output_name,
                    output_extension="mp4",
                    intervals=intervals
                )
            else:
                continue
            
            tasks.append(task)
        
        global_settings = {
            "output_extension": "mp4",
            "video_codec": "copy",
            "audio_codec": "copy"
        }
        
        return manager.create_config(tasks, global_settings)

class WorkflowBuilder:
    """Builder for creating complex workflows"""
    
    def __init__(self):
        self.manager = ConfigurationManager()
        self.tasks: List[TaskConfig] = []
        self.global_settings: Dict[str, Any] = {}
    
    def add_download(self, url: str, output_filename: str) -> 'WorkflowBuilder':
        """Add download task to workflow"""
        task = self.manager.create_download_task(url, output_filename)
        self.tasks.append(task)
        return self
    
    def add_split(self, source_file: str, output_name: str, max_size: str,
                  output_extension: str = "mp4") -> 'WorkflowBuilder':
        """Add split task to workflow"""
        task = self.manager.create_split_task(source_file, output_name, output_extension, max_size)
        self.tasks.append(task)
        return self
    
    def add_clip(self, source_file: str, output_name: str, intervals: List[Dict[str, Any]],
                 output_extension: str = "mp4", video_codec: str = "copy", 
                 audio_codec: str = "copy") -> 'WorkflowBuilder':
        """Add clip task to workflow"""
        task = self.manager.create_clip_task(
            source_file, output_name, output_extension, intervals, video_codec, audio_codec
        )
        self.tasks.append(task)
        return self
    
    def set_global_setting(self, key: str, value: Any) -> 'WorkflowBuilder':
        """Set global setting"""
        self.global_settings[key] = value
        return self
    
    def set_default_codec(self, video_codec: str = "copy", audio_codec: str = "copy") -> 'WorkflowBuilder':
        """Set default codecs"""
        self.global_settings["video_codec"] = video_codec
        self.global_settings["audio_codec"] = audio_codec
        return self
    
    def set_default_extension(self, extension: str = "mp4") -> 'WorkflowBuilder':
        """Set default output extension"""
        self.global_settings["output_extension"] = extension
        return self
    
    def build(self) -> ProcessingConfig:
        """Build the complete configuration"""
        return self.manager.create_config(self.tasks, self.global_settings)
    
    def clear(self) -> 'WorkflowBuilder':
        """Clear all tasks and settings"""
        self.tasks.clear()
        self.global_settings.clear()
        return self

# Convenience functions for common workflows
def create_download_split_workflow(url: str, output_name: str, max_size: str = "2GB") -> ProcessingConfig:
    """Create download + split workflow"""
    return (WorkflowBuilder()
            .add_download(url, f"{output_name}_raw.mp4")
            .add_split(f"{output_name}_raw.mp4", f"{output_name}_part", max_size)
            .set_default_extension("mp4")
            .build())

def create_multi_clip_workflow(source_file: str, clips_config: List[Dict[str, Any]]) -> ProcessingConfig:
    """Create multiple clips from same source"""
    builder = WorkflowBuilder()
    
    for i, clip_config in enumerate(clips_config):
        output_name = clip_config.get("output_name", f"clip_{i+1}")
        intervals = clip_config.get("intervals", [])
        video_codec = clip_config.get("video_codec", "copy")
        audio_codec = clip_config.get("audio_codec", "copy")
        
        builder.add_clip(source_file, output_name, intervals, "mp4", video_codec, audio_codec)
    
    return builder.set_default_extension("mp4").build()
