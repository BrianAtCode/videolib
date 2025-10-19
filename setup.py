"""
VideoLib - Professional Video Processing Library
================================================

A comprehensive Python library for video splitting and clipping operations 
with FFmpeg integration.

Author: Kam ho, brian
License: MIT
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="videolib",
    version="1.0.0",
    author="Kam ho, brian",
    description="Professional video processing library with FFmpeg integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BrianAtCode/videolib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No Python package dependencies
        # Only requires FFmpeg (external tool)
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=4.0", "black>=22.0", "flake8>=5.0"],
    },
    entry_points={
        "console_scripts": [
            # Library doesn't provide CLI commands
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="video processing ffmpeg video-editing video-converter video-splitter video-clipper",
    project_urls={
        "Bug Reports": "https://github.com/BrianAtCode/videolib/issues",
        "Source": "https://github.com/BrianAtCode/videolib",
        "Documentation": "https://github.com/BrianAtCode/videolib#readme",
    },
)
