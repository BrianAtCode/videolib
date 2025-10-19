"""
Configuration management for video processing
"""
from .config_manager import (
    ConfigurationManager, TaskConfig, ProcessingConfig,
    load_config_from_file, create_simple_download_config,
    create_simple_split_config, create_simple_clip_config
)
from .task_definitions import (
    TaskTemplates, WorkflowBuilder,
    create_download_split_workflow, create_multi_clip_workflow
)

__all__ = [
    # Core classes
    'ConfigurationManager',
    'TaskConfig', 
    'ProcessingConfig',
    
    # Convenience functions
    'load_config_from_file',
    'create_simple_download_config',
    'create_simple_split_config', 
    'create_simple_clip_config',
    
    # Templates and workflows
    'TaskTemplates',
    'WorkflowBuilder',
    'create_download_split_workflow',
    'create_multi_clip_workflow'
]
