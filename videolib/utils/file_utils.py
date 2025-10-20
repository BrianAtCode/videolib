"""
File utility functions for video processing
"""
import os
import shutil
from typing import List, Optional
from urllib.parse import urlparse

class FileManager:
    """File management utilities"""
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Ensure directory exists, create if necessary"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError:
            return False
    
    @staticmethod
    def get_unique_filename(base_path: str, extension: str) -> str:
        """Generate unique filename to avoid conflicts"""
        if not extension.startswith('.'):
            extension = '.' + extension
        
        base_name = base_path
        counter = 1
        
        while os.path.exists(base_name + extension):
            # Try with counter suffix
            test_name = f"{base_path}_{counter:03d}"
            if not os.path.exists(test_name + extension):
                return test_name
            counter += 1
            
            # Prevent infinite loop
            if counter > 9999:
                break
        
        return base_name
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        """Copy file with error handling"""
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(source, destination)
            return True
        except (OSError, shutil.Error):
            return False
    
    @staticmethod
    def move_file(source: str, destination: str) -> bool:
        """Move/rename file with error handling"""
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(source, destination)
            return True
        except (OSError, shutil.Error):
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file with error handling"""
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return None
    
    @staticmethod
    def get_basename(file_path: str) -> str:
        """Get basename (filename with extension) from file path"""
        return os.path.basename(file_path)
    
    @staticmethod
    def list_files_with_pattern(directory: str, prefix: str, extension: str) -> List[str]:
        """List files matching prefix and extension pattern"""
        try:
            files = []
            for file in os.listdir(directory):
                if file.startswith(prefix) and file.endswith('.' + extension):
                    files.append(os.path.join(directory, file))
            return sorted(files)
        except OSError:
            return []
    
    @staticmethod
    def suggest_filename_from_url(url: str, default: str = "downloaded_video.mp4") -> str:
        """Extract filename from URL or return default"""
        try:
            parsed = urlparse(url)
            basename = os.path.basename(parsed.path)
            if basename and '.' in basename:
                return basename
        except Exception:
            pass
        return default
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension without the dot"""
        return os.path.splitext(file_path)[1][1:].lower()
    
    @staticmethod
    def change_extension(file_path: str, new_extension: str) -> str:
        """Change file extension"""
        base = os.path.splitext(file_path)[0]
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension
        return base + new_extension