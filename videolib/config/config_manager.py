"""
Configuration management for video processing operations
"""
import json
import os
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from ..utils import InputValidator, ConfigValidator, ValidationError

@dataclass
class TaskConfig:
    """Configuration for a single task"""
    task_type: str  # 'download', 'split', 'clip'
    parameters: Dict[str, Any]
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate task configuration"""
        if self.task_type == 'download':
            return ConfigValidator.validate_download_config(self.parameters)
        elif self.task_type == 'split':
            return ConfigValidator.validate_split_config(self.parameters)
        elif self.task_type == 'clip':
            return ConfigValidator.validate_clip_config(self.parameters)
        else:
            return False, [f"Unknown task type: {self.task_type}"]

@dataclass
class ProcessingConfig:
    """Complete configuration for video processing"""
    tasks: List[TaskConfig]
    global_settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.global_settings is None:
            self.global_settings = {}
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate complete configuration"""
        errors = []
        
        if not self.tasks:
            errors.append("No tasks specified")
            return False, errors
        
        # Validate each task
        for i, task in enumerate(self.tasks):
            is_valid, task_errors = task.validate()
            if not is_valid:
                for error in task_errors:
                    errors.append(f"Task {i+1}: {error}")
        
        return len(errors) == 0, errors
    
    def get_merged_params(self, task_index: int) -> Dict[str, Any]:
        """Get task parameters merged with global settings"""
        if task_index >= len(self.tasks):
            raise IndexError(f"Task index {task_index} out of range")
        
        # Start with global settings
        merged = self.global_settings.copy()
        
        # Override with task-specific parameters
        merged.update(self.tasks[task_index].parameters)
        
        return merged

class ConfigurationManager:
    """Manage video processing configurations"""
    
    def __init__(self):
        self.current_config: Optional[ProcessingConfig] = None
    
    def load_from_dict(self, config_dict: Dict[str, Any]) -> ProcessingConfig:
        """Load configuration from dictionary"""
        # Parse tasks
        tasks = []
        if 'tasks' not in config_dict:
            raise ValidationError("Configuration must contain 'tasks' field")
        
        for i, task_data in enumerate(config_dict['tasks']):
            if not isinstance(task_data, dict):
                raise ValidationError(f"Task {i+1} must be a dictionary")
            
            if 'type' not in task_data:
                raise ValidationError(f"Task {i+1} missing 'type' field")
            
            if 'parameters' not in task_data:
                raise ValidationError(f"Task {i+1} missing 'parameters' field")
            
            task = TaskConfig(
                task_type=task_data['type'],
                parameters=task_data['parameters']
            )
            tasks.append(task)
        
        # Create configuration
        config = ProcessingConfig(
            tasks=tasks,
            global_settings=config_dict.get('global_settings', {})
        )
        
        # Validate
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValidationError("Configuration validation failed: " + "; ".join(errors))
        
        self.current_config = config
        return config
    
    def load_from_file(self, file_path: str) -> ProcessingConfig:
        """Load configuration from JSON file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValidationError(f"Error reading configuration file: {e}")
        
        return self.load_from_dict(config_dict)
    
    def save_to_file(self, config: ProcessingConfig, file_path: str) -> None:
        """Save configuration to JSON file"""
        config_dict = self._config_to_dict(config)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValidationError(f"Error writing configuration file: {e}")
    
    def _config_to_dict(self, config: ProcessingConfig) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        tasks_list = []
        for task in config.tasks:
            tasks_list.append({
                'type': task.task_type,
                'parameters': task.parameters
            })
        
        config_dict = {
            'tasks': tasks_list
        }
        
        if config.global_settings:
            config_dict['global_settings'] = config.global_settings
        
        return config_dict
    
    def create_download_task(self, url: str, output_filename: str) -> TaskConfig:
        """Create download task configuration"""
        return TaskConfig(
            task_type='download',
            parameters={
                'url': url,
                'output_filename': output_filename
            }
        )
    
    def create_split_task(self, source_file: str, output_name: str, 
                         output_extension: str, max_size: str) -> TaskConfig:
        """Create split task configuration"""
        return TaskConfig(
            task_type='split',
            parameters={
                'source_file': source_file,
                'output_name': output_name,
                'output_extension': output_extension,
                'max_size': max_size
            }
        )
    
    def create_clip_task(self, source_file: str, output_name: str,
                        output_extension: str, intervals: List[Dict[str, Any]],
                        video_codec: str = 'copy', audio_codec: str = 'copy') -> TaskConfig:
        """Create clip task configuration"""
        return TaskConfig(
            task_type='clip',
            parameters={
                'source_file': source_file,
                'output_name': output_name,
                'output_extension': output_extension,
                'intervals': intervals,
                'video_codec': video_codec,
                'audio_codec': audio_codec
            }
        )
    
    def create_config(self, tasks: List[TaskConfig], 
                     global_settings: Optional[Dict[str, Any]] = None) -> ProcessingConfig:
        """Create complete processing configuration"""
        return ProcessingConfig(tasks=tasks, global_settings=global_settings)
    
    def validate_config_file(self, file_path: str) -> tuple[bool, List[str]]:
        """Validate configuration file without loading it"""
        try:
            config = self.load_from_file(file_path)
            return True, []
        except (ValidationError, FileNotFoundError) as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Unexpected error: {e}"]

# Convenience functions
def load_config_from_file(file_path: str) -> ProcessingConfig:
    """Load configuration from file (convenience function)"""
    manager = ConfigurationManager()
    return manager.load_from_file(file_path)

def create_simple_download_config(url: str, output_filename: str) -> ProcessingConfig:
    """Create simple download configuration"""
    manager = ConfigurationManager()
    task = manager.create_download_task(url, output_filename)
    return manager.create_config([task])

def create_simple_split_config(source_file: str, output_name: str, 
                              max_size: str, output_extension: str = 'mp4') -> ProcessingConfig:
    """Create simple split configuration"""
    manager = ConfigurationManager()
    task = manager.create_split_task(source_file, output_name, output_extension, max_size)
    return manager.create_config([task])

def create_simple_clip_config(source_file: str, output_name: str,
                             intervals: List[Dict[str, Any]], 
                             output_extension: str = 'mp4') -> ProcessingConfig:
    """Create simple clip configuration"""
    manager = ConfigurationManager()
    task = manager.create_clip_task(source_file, output_name, output_extension, intervals)
    return manager.create_config([task])
