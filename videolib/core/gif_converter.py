import os
import time
import json
from typing import List, Tuple, Optional, Dict

# PIL for grid creation (optional)
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from ..interfaces.gif_interface import (
    GifConverterInterface, GifOptions, GifResult, GifInterval, AutoGifOptions
)
from .ffmpeg_wrapper import (
    FFmpegWrapper, FFmpegResult, MediaInfo,
    ClipCommand, GifOrdinaryCommand, GifColorPaletteCommand, 
    ThumbnailCommand, ColorPaletteCommand
)


class VideoGifConverter(GifConverterInterface):
    """Enhanced Video to GIF converter using video-clips-first workflow"""

    def __init__(self, ffmpeg_wrapper: FFmpegWrapper = None):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()

    def create_gifs(self, options: GifOptions) -> GifResult:
        """Create multiple GIF clips from video using traditional workflow"""
        start_time = time.time()
        
        try:
            if not self._validate_options(options):
                return self._error_result("Invalid options", start_time)

            gif_files = []
            thumbnail_files = []

            # Generate palette for better quality
            palette_file = self._create_palette(options) if options.quality_level == "high" else None

            # Process each interval - traditional single GIF approach
            for interval in options.intervals:
                # Create GIF directly from source
                gif_file = self._create_gif(interval, options, palette_file)
                if gif_file:
                    gif_files.append(gif_file)

                    # Create thumbnail if requested
                    if options.create_thumbnails:
                        thumb_file = self._create_thumbnail(gif_file, interval.output_name, options.thumbnail_extension)
                        if thumb_file:
                            thumbnail_files.append(thumb_file)

            # Cleanup palette
            if palette_file and os.path.exists(palette_file):
                os.remove(palette_file)

            return GifResult(
                success=len(gif_files) > 0,
                gif_files=gif_files,
                thumbnail_files=thumbnail_files,
                total_duration=sum(i.end_time - i.start_time for i in options.intervals),
                processing_time=time.time() - start_time
            )

        except Exception as e:
            return self._error_result(str(e), start_time)

    def create_gif_from_intervals(self, source_file: str, intervals: List[Tuple[float, float]],
                                output_name: str, **kwargs) -> GifResult:
        """Create GIFs from time intervals using traditional workflow"""
        gif_intervals = [
            GifInterval(start, end, f"{output_name}_{i+1:03d}")
            for i, (start, end) in enumerate(intervals)
        ]
        
        options = GifOptions(source_file=source_file, intervals=gif_intervals, **kwargs)
        return self.create_gifs(options)

    def create_auto_generated_clips(self, options: AutoGifOptions) -> GifResult:
        """Create auto-generated GIF clips using NEW video-clips-first workflow"""
        start_time = time.time()
        
        try:
            # Step 1: Calculate intervals with time gaps
            intervals = self._calculate_auto_intervals(options)
            
            # Step 2: Create video clips first using ClipCommand
            video_clips = self._create_video_clips(options.source_file, intervals)
            if not video_clips:
                return self._error_result("Failed to create video clips", start_time)
            
            # Step 3: Create thumbnails from video clips (not GIFs)
            thumbnail_files = []
            if options.create_thumbnails:
                thumbnail_files = self._create_thumbnails_from_videos(video_clips, intervals)
            
            # Step 4: Merge all video clips into one video
            merged_video = self._merge_video_clips(video_clips, f"{options.output_name}_merged.mp4")
            if not merged_video:
                return self._error_result("Failed to merge video clips", start_time)
            
            # Step 5: Convert merged video to GIF with media info
            gif_files = []
            if merged_video:
                gif_file = self._convert_video_to_gif(merged_video, options)
                if gif_file:
                    gif_files.append(gif_file)
            
            # Step 6: Get media info and create enhanced results
            media_info = self._get_media_info_dict(options.source_file)
            
            # Step 7: Create enhanced thumbnail grid
            grid_file = None
            if options.create_grid and thumbnail_files and PIL_AVAILABLE:
                grid_file = self._create_enhanced_grid(
                    thumbnail_files, 
                    media_info,
                    f"{options.output_name}_grid.png",
                    options.grid_size, 
                    intervals,
                    options=options 
                )
                if grid_file:
                    thumbnail_files.append(grid_file)
            
            #Cleanup individual thumbnails if requested
            if options.cleanup_individual_thumbs and grid_file and thumbnail_files:
                cleaned_thumbnails = self._cleanup_individual_thumbnails(thumbnail_files, grid_file)
                thumbnail_files = cleaned_thumbnails

            # Cleanup temporary video clips
            for clip in video_clips:
                if os.path.exists(clip):
                    os.remove(clip)
            if merged_video and os.path.exists(merged_video):
                os.remove(merged_video)
            
            result = GifResult(
                success=len(gif_files) > 0,
                gif_files=gif_files,
                thumbnail_files=thumbnail_files,
                total_duration=sum(i.end_time - i.start_time for i in intervals),
                processing_time=time.time() - start_time,
                media_info=media_info
            )
            
            return result
            
        except Exception as e:
            return self._error_result(str(e), start_time)
        
    def create_one_click_gif(self, source_file: str, output_name: str = "oneclick") -> GifResult:
        """One-click video to GIF conversion with automatic settings"""
        start_time = time.time()
        
        try:
            # Get video duration
            media_info_result = self.ffmpeg.probe_media(source_file)
            if not media_info_result.success or not media_info_result.media_info:
                return self._error_result("Could not analyze video file", start_time)
            
            total_duration = media_info_result.media_info.duration
            if not total_duration or total_duration <= 0:
                return self._error_result("Invalid video duration", start_time)
            
            # AUTOMATIC SETTINGS CALCULATION
            num_clips = 30  # Fixed number of clips as requested
            
            # Calculate optimal clip duration and gap
            if total_duration <= 30:
                # Short video: Use 1-second clips with no gap
                gif_duration = 1.0
                time_gap = max(0, (total_duration - num_clips) / (num_clips - 1)) if num_clips > 1 else 0
            elif total_duration <= 300:  # 5 minutes
                # Medium video: Use 2-second clips with small gaps
                gif_duration = 2.0
                time_gap = max(0, (total_duration - (num_clips * gif_duration)) / (num_clips - 1)) if num_clips > 1 else 0
            else:
                # Long video: Use 3-second clips with calculated gaps to cover full duration
                gif_duration = 3.0
                time_gap = max(0, (total_duration - (num_clips * gif_duration)) / (num_clips - 1)) if num_clips > 1 else 0
            
            #Calculate optimal gif resolution (max 1440x1080)
            final_width, final_height = self._get_optimal_final_resolution(source_file, 720, 360)

            # Calculate optimal grid resolution (max 1440x1080 total)
            grid_thumb_width, grid_thumb_height = self._get_optimal_grid_resolution(30, 6)  # 30 clips, 6x5 grid
            
            print(f"🚀 One-Click Auto Settings:")
            print(f"   Video Duration: {self._format_duration(total_duration)}")
            print(f"   Clips: {num_clips} clips of {gif_duration}s each")
            print(f"   Time Gap: {time_gap:.1f}s between clips")
            print(f"   Final GIF Resolution: {final_width}x{final_height}") 
            print(f"   Grid Thumbnail Size: {grid_thumb_width}x{grid_thumb_height}")
            print(f"   Coverage: {self._format_duration(num_clips * gif_duration + (num_clips-1) * time_gap)}")
            print()
            
            # Create auto options with optimal settings
            options = AutoGifOptions(
                source_file=source_file,
                num_clips=num_clips,
                gif_duration=gif_duration,
                time_gap=time_gap,
                output_name=output_name,
                fps=12,  # Good balance of quality and size
                scale_width=480,  # Reasonable resolution
                quality_level="medium",  # Balanced quality
                create_thumbnails=True,
                create_grid=True,
                merge_gifs=False,  # Use video-first workflow (no GIF merging)
                grid_size=6,  # 6x5 grid for 30 clips
                cleanup_individual_thumbs=True,  # Clean output by default
                final_gif_width=final_width,   # Final GIF resolution
                final_gif_height=final_height, # Final GIF resolution
                grid_thumb_width=grid_thumb_width,    # thumbnail width
                grid_thumb_height=grid_thumb_height,  # thumbnail height
                grid_max_width=1440,                  # Max grid width
                grid_max_height=1080                  # Max grid height    
            )
            
            # Use the existing auto-generation workflow
            return self.create_auto_generated_clips(options)
            
        except Exception as e:
            return self._error_result(str(e), start_time)

    def _get_optimal_grid_resolution(self, num_clips: int, cols: int) -> Tuple[int, int]:
        """Calculate optimal thumbnail size for grid within 1440x1080 limit"""
        rows = (num_clips + cols - 1) // cols
        header_height = 150
        
        # Calculate maximum thumbnail size that fits in 1440x1080
        max_thumb_width = 1440 // cols
        max_thumb_height = (1080 - header_height) // rows
        
        # Use 16:9 aspect ratio for thumbnails, but respect limits
        target_width = min(240, max_thumb_width)  # Prefer 240px width
        target_height = int(target_width * 9 / 16)  # 16:9 aspect ratio
        
        # Ensure height fits
        if target_height > max_thumb_height:
            target_height = max_thumb_height
            target_width = int(target_height * 16 / 9)
        
        # Ensure minimum readable size
        target_width = max(120, target_width)
        target_height = max(68, target_height)
        
        return target_width, target_height

    def _cleanup_individual_thumbnails(self, thumbnail_files: List[str], grid_file: str) -> List[str]:
        """Remove individual thumbnail files, keeping only the grid file"""
        cleaned_files = []
        removed_count = 0
        
        for thumb_file in thumbnail_files:
            if thumb_file == grid_file:
                # Keep the grid file
                cleaned_files.append(thumb_file)
            elif thumb_file.endswith('_grid.png'):
                # Keep any grid files
                cleaned_files.append(thumb_file)
            else:
                # Remove individual thumbnail files
                try:
                    if os.path.exists(thumb_file):
                        os.remove(thumb_file)
                        removed_count += 1
                        print(f"Removed individual thumbnail: {thumb_file}")
                except Exception as e:
                    print(f"Warning: Could not remove {thumb_file}: {e}")
                    # Keep the file if we can't remove it
                    cleaned_files.append(thumb_file)
        
        if removed_count > 0:
            print(f"✅ Cleaned up {removed_count} individual thumbnail file(s), kept grid file")
        
        return cleaned_files
    
    def _create_video_clips(self, source_file: str, intervals: List[GifInterval]) -> List[str]:
        """Create video clips using ClipCommand from ffmpeg_wrapper"""
        video_clips = []
        
        for i, interval in enumerate(intervals):
            clip_file = f"temp_clip_{i+1:03d}.mp4"
            
            # Use your existing ClipCommand
            clip_cmd = ClipCommand(
                wrapper=self.ffmpeg,
                input_path=source_file,
                output_path=clip_file,
                start_time=interval.start_time,
                end_time=interval.end_time,
                video_codec="copy",  # Fast copy without re-encoding
                audio_codec="copy"
            )
            
            result = clip_cmd.execute()
            if result.success and os.path.exists(clip_file):
                video_clips.append(clip_file)
            else:
                print(f"Warning: Failed to create clip {clip_file}")
        
        return video_clips

    def _create_thumbnails_from_videos(self, video_clips: List[str], intervals: List[GifInterval]) -> List[str]:
        """Create thumbnails from video clips (not GIFs)"""
        thumbnail_files = []
        
        for video_clip, interval in zip(video_clips, intervals):
            thumb_file = f"{interval.output_name}_thumb.png"
            
            # Use existing ThumbnailCommand to extract first frame from video
            thumb_cmd = ThumbnailCommand(self.ffmpeg, video_clip, thumb_file)
            result = thumb_cmd.execute()
            
            if result.success and os.path.exists(thumb_file):
                thumbnail_files.append(thumb_file)
            else:
                print(f"Warning: Failed to create thumbnail from {video_clip}")
        
        return thumbnail_files

    def _merge_video_clips(self, video_clips: List[str], output_file: str) -> Optional[str]:
        """Merge multiple video clips into one video using FFmpeg concat"""
        try:
            if not video_clips:
                return None
            
            # Create concat file for FFmpeg
            concat_file = "temp_video_concat.txt"
            
            with open(concat_file, 'w') as f:
                for clip in video_clips:
                    # Escape file paths for FFmpeg
                    escaped_path = clip.replace('\\', '\\\\').replace("'", "\\'")
                    f.write(f"file '{escaped_path}' \n")
            
            # Use FFmpeg concat demuxer to merge videos
            import subprocess
            cmd = [
                self.ffmpeg.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",  # Copy streams without re-encoding
                "-y", output_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Cleanup
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            return output_file if os.path.exists(output_file) else None
            
        except Exception as e:
            print(f"Video merge failed: {e}")
            return None

    def _convert_video_to_gif(self, video_file: str, options: AutoGifOptions) -> Optional[str]:
        """Convert merged video to GIF with embedded media info"""
        gif_file = f"{options.output_name}_final.gif"
        
        try:
            # Build quality filters
            filters = self._build_quality_filters_for_auto(options)
            
            # Create palette for high quality
            palette_file = None
            if options.quality_level == "high":
                palette_file = "temp_final_palette.png"
                palette_cmd = ColorPaletteCommand(self.ffmpeg, video_file, palette_file, filters)
                if not palette_cmd.execute().success:
                    palette_file = None
            
            # Convert to GIF
            if palette_file and os.path.exists(palette_file):
                # High quality with palette
                gif_cmd = GifColorPaletteCommand(
                    wrapper=self.ffmpeg,
                    input_path=video_file,
                    output_path=gif_file,
                    start_time=0.0,  # Use entire merged video
                    palette_file=palette_file,
                    duration=0.0,  # 0 means use entire video
                    filters=filters,
                    loop_count=0  # Infinite loop
                )
            else:
                # Standard quality
                gif_cmd = GifOrdinaryCommand(
                    wrapper=self.ffmpeg,
                    input_path=video_file,
                    output_path=gif_file,
                    start_time=0.0,
                    duration=0.0,  # Use entire video
                    filters=filters,
                    loop_count=0
                )
            
            result = gif_cmd.execute()
            
            # Cleanup palette
            if palette_file and os.path.exists(palette_file):
                os.remove(palette_file)
            
            return gif_file if result.success else None
            
        except Exception as e:
            print(f"Video to GIF conversion failed: {e}")
            return None

    # --- TRADITIONAL WORKFLOW METHODS (renamed) ---

    def _create_gif(self, interval: GifInterval, options: GifOptions, 
                   palette_file: Optional[str]) -> Optional[str]:
        """Create single GIF using traditional workflow (renamed from _create_single_gif)"""
        output_file = f"{interval.output_name}.{options.output_extension}"
        duration = interval.end_time - interval.start_time
        filters = self._build_quality_filters(options)

        if palette_file and os.path.exists(palette_file):
            # Use high-quality palette command
            cmd = GifColorPaletteCommand(
                wrapper=self.ffmpeg,
                input_path=options.source_file,
                output_path=output_file,
                start_time=interval.start_time,
                palette_file=palette_file,
                duration=duration,
                filters=filters,
                loop_count=options.loop_count
            )
        else:
            # Use ordinary command
            cmd = GifOrdinaryCommand(
                wrapper=self.ffmpeg,
                input_path=options.source_file,
                output_path=output_file,
                start_time=interval.start_time,
                duration=duration,
                filters=filters,
                loop_count=options.loop_count
            )

        result = cmd.execute()
        return output_file if result.success else None

    # --- HELPER METHODS ---

    def _validate_options(self, options: GifOptions) -> bool:
        """Basic validation"""
        return (options.source_file and 
                os.path.exists(options.source_file) and 
                options.intervals and
                all(i.start_time < i.end_time for i in options.intervals))

    def _calculate_auto_intervals(self, options: AutoGifOptions) -> List[GifInterval]:
        """Calculate sequential intervals with time gaps"""
        intervals = []
        current_start = 0.0
        
        for i in range(options.num_clips):
            intervals.append(GifInterval(
                start_time=current_start,
                end_time=current_start + options.gif_duration,
                output_name=f"{options.output_name}_{i+1:03d}"
            ))
            current_start += options.gif_duration + options.time_gap
        
        return intervals

    def _create_palette(self, options: GifOptions) -> Optional[str]:
        """Create color palette using existing command"""
        palette_file = "temp_palette.png"
        filters = self._build_quality_filters(options)
        
        cmd = ColorPaletteCommand(self.ffmpeg, options.source_file, palette_file, filters)
        result = cmd.execute()
        
        return palette_file if result.success else None

    def _create_thumbnail(self, source_file: str, output_name: str, extension: str) -> Optional[str]:
        """Create thumbnail using existing command"""
        thumb_file = f"{output_name}_thumb.{extension}"
        cmd = ThumbnailCommand(self.ffmpeg, source_file, thumb_file)
        result = cmd.execute()
        return thumb_file if result.success else None

    def _build_quality_filters(self, options: GifOptions) -> str:
        """Build FFmpeg filters based on quality for traditional workflow"""
        base = f"fps={options.fps},scale={options.scale_width}:-1:flags=lanczos"
        
        if options.quality_level == "high":
            return f"{base},mpdecimate"
        elif options.quality_level == "low":
            return f"{base},mpdecimate=hi=64*12:lo=64*5:frac=0.1"
        return base

    def _build_quality_filters_for_auto(self, options: AutoGifOptions) -> str:
        """Build FFmpeg filters based on quality for auto workflow"""
        # Use final resolution settings
        final_width = options.final_gif_width
        final_height = options.final_gif_height
            
        # Calculate height automatically if not specified
        if final_height <= 0:
            scale_filter = f"scale={final_width}:-1:flags=lanczos"
        else:
            scale_filter = f"scale={final_width}:{final_height}:flags=lanczos"
        
        base = f"fps={options.fps},{scale_filter}"
        
        if options.quality_level == "high":
            return f"{base},mpdecimate"
        elif options.quality_level == "low":
            return f"{base},mpdecimate=hi=64*12:lo=64*5:frac=0.1"
        return base

    def _get_optimal_final_resolution(self, source_file: str, max_width: int = 1440, max_height: int = 1080) -> Tuple[int, int]:
        """Calculate optimal final resolution based on source video and limits"""
        try:
            # Get source video resolution
            media_info_result = self.ffmpeg.probe_media(source_file)
            if media_info_result.success and media_info_result.media_info:
                source_width = media_info_result.media_info.width or 1920
                source_height = media_info_result.media_info.height or 1080
            else:
                # Fallback resolution
                source_width, source_height = 1920, 1080
            
            # Calculate scaling to fit within max dimensions while maintaining aspect ratio
            width_scale = max_width / source_width
            height_scale = max_height / source_height
            scale = min(width_scale, height_scale, 1.0)  # Don't upscale
            
            final_width = int(source_width * scale)
            final_height = int(source_height * scale)
            
            # Ensure even dimensions (required for some codecs)
            final_width = final_width - (final_width % 2)
            final_height = final_height - (final_height % 2)
            
            return final_width, final_height
            
        except Exception as e:
            print(f"Warning: Could not determine optimal resolution: {e}")
            return max_width, max_height

    def _get_media_info_dict(self, source_file: str) -> Dict[str, str]:
        """Get media info using existing wrapper"""
        result = self.ffmpeg.probe_media(source_file)
        
        if result.success and result.media_info:
            info = result.media_info
            file_stat = os.stat(source_file) if os.path.exists(source_file) else None
            
            return {
                'filename': os.path.basename(source_file),
                'format': (info.format_name or 'Unknown').upper(),
                'duration': str(info.duration or 0),
                'size': str(info.size_bytes or 0),
                'creation_time': time.ctime(file_stat.st_ctime) if file_stat else 'Unknown',
                'video_codec': (info.video_codec or 'Unknown').upper(),
                'audio_codec': (info.audio_codec or 'Unknown').upper(),
                'width': str(info.width or 0),
                'height': str(info.height or 0)
            }
        
        # Fallback
        return {'filename': os.path.basename(source_file), 'format': 'Unknown', 'duration': '0', 
                'size': '0', 'creation_time': 'Unknown', 'video_codec': 'Unknown', 
                'audio_codec': 'Unknown', 'width': '0', 'height': '0'}

    def _create_enhanced_grid(self, thumb_files: List[str], media_info: Dict[str, str],
                            output_file: str, grid_size: int, intervals: Optional[List[GifInterval]] = None, 
                            options: Optional[AutoGifOptions] = None) -> Optional[str]:
        """Create thumbnail grid with media info (requires PIL)"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            if not thumb_files:
                return None
            
            # Calculate grid layout with resolution control
            grid_layout = self._calculate_grid_layout(thumb_files, grid_size, options)

            # Load first thumbnail for dimensions
            first_thumb = Image.open(thumb_files[0])
            w, h = first_thumb.size
            first_thumb.close()
            
            # Use calculated thumbnail dimensions
            thumb_width = grid_layout['thumb_width']
            thumb_height = grid_layout['thumb_height']
            cols = grid_layout['cols']
            rows = grid_layout['rows']
            
            # Create canvas with header space
            header_height = 150
            canvas_width = cols * thumb_width
            canvas_height = rows * thumb_height + header_height
            
            #Apply maximum grid size limits
            if options and (canvas_width > options.grid_max_width or canvas_height > options.grid_max_height):
                scale_factor = min(
                    options.grid_max_width / canvas_width,
                    options.grid_max_height / canvas_height
                )
                
                # Recalculate with scaling
                thumb_width = int(thumb_width * scale_factor)
                thumb_height = int(thumb_height * scale_factor)
                canvas_width = cols * thumb_width
                canvas_height = rows * thumb_height + int(header_height * scale_factor)
                header_height = int(header_height * scale_factor)
                
                print(f"📏 Scaled to fit limits: {canvas_width}x{canvas_height} (scale: {scale_factor:.2f})")
            
            # Create canvas
            canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
            draw = ImageDraw.Draw(canvas)

            # Scale fonts based on grid size
            font_scale = min(1.0, canvas_width / 1200)  # Scale fonts for smaller grids
            title_size = max(12, int(18 * font_scale))
            info_size = max(10, int(14 * font_scale))
            timestamp_size = max(8, int(12 * font_scale))
            
            # Load fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", title_size)
                info_font = ImageFont.truetype("arial.ttf", info_size)
                timestamp_font = ImageFont.truetype("arial.ttf", timestamp_size) 
            except:
                title_font = info_font = timestamp_font = ImageFont.load_default()
            
            # Draw header with media info
            y = 15
            draw.text((15, y), f"Video: {media_info['filename']}", fill=(0,0,0), font=title_font)
            y += 30
            
            # Format info lines
            duration_str = self._format_duration(float(media_info['duration']))
            size_str = self._format_file_size(int(media_info['size']))

            info_lines = [
                f"Format: {media_info['format']} | Codec: {media_info['video_codec']}",
                f"Duration: {duration_str} | Size: {size_str}",
                f"Resolution: {media_info['width']}x{media_info['height']}",
                f"Grid: {cols}x{rows} ({len(thumb_files)} thumbnails)",
                f"Created: {media_info['creation_time'][:10]}"
            ]
            
            for line in info_lines:
                draw.text((int(15 * font_scale), y), line, fill=(64,64,64), font=info_font)
                y += int(20 * font_scale)
            
            # Paste thumbnails
            for i, thumb_file in enumerate(thumb_files[:grid_size*grid_size]):
                if not os.path.exists(thumb_file):
                    print(f"Warning: Thumbnail file not found: {thumb_file}")
                    continue
                    
                row, col = divmod(i, cols)
                x, y = col * thumb_width, row * thumb_height + header_height
                
                try:
                    thumb = Image.open(thumb_file)
                    # ✅ NEW: Use calculated thumbnail dimensions
                    thumb = thumb.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                    canvas.paste(thumb, (x, y))
                    thumb.close()
                    
                    # ✅ NEW: Scale timestamp and frame number positioning
                    timestamp_text = self._get_thumbnail_timestamp(i, intervals)
                    
                    # Calculate text sizes
                    timestamp_width = len(timestamp_text) * max(6, int(7 * font_scale))
                    timestamp_height = max(10, int(14 * font_scale))
                    
                    # Position timestamp at bottom-left
                    timestamp_x = x + int(5 * font_scale)
                    timestamp_y = y + thumb_height - timestamp_height - int(5 * font_scale)
                    
                    # Draw timestamp background and text
                    draw.rectangle([
                        timestamp_x - 2, timestamp_y - 1,
                        timestamp_x + timestamp_width + 2, timestamp_y + timestamp_height + 1
                    ], fill=(0, 0, 0))
                    
                    draw.text((timestamp_x, timestamp_y), timestamp_text, 
                            fill=(255, 255, 255), font=timestamp_font)
                    
                    # Frame number in top-right
                    frame_text = f"#{i+1}"
                    frame_width = len(frame_text) * max(6, int(8 * font_scale))
                    frame_height = max(10, int(14 * font_scale))
                    
                    frame_x = x + thumb_width - frame_width - int(8 * font_scale)
                    frame_y = y + int(5 * font_scale)
                    
                    draw.rectangle([
                        frame_x - 2, frame_y - 1,
                        frame_x + frame_width + 2, frame_y + frame_height + 1
                    ], fill=(0, 100, 200))
                    
                    draw.text((frame_x, frame_y), frame_text, 
                            fill=(255, 255, 255), font=info_font)
                    
                except Exception as e:
                    print(f"Warning: Failed to process thumbnail {thumb_file}: {e}")
                    continue
            
            # Save grid image with high quality
            canvas.save(output_file, 'PNG', quality=95, optimize=True)
            canvas.close()
            return output_file
            
        except Exception as e:
            print(f"Grid creation failed: {e}")
            return None
        
    def _get_text_size(self, draw, text: str, font) -> Tuple[int, int]:
        """Safely get text dimensions with fallback methods"""
        try:
            # Method 1: Try textbbox (PIL 8.0.0+)
            bbox = draw.textbbox((0, 0), text, font=font)
            if bbox is not None and len(bbox) >= 4:
                width = bbox - bbox
                height = bbox - bbox
                return (width, height)
        except (AttributeError, TypeError, ValueError):
            pass
        
        try:
            # Method 2: Try textsize (older PIL versions)
            if hasattr(draw, 'textsize'):
                return draw.textsize(text, font=font)
        except (AttributeError, TypeError, ValueError):
            pass
        
        # Method 3: Fallback estimation
        char_width = 8 if font == ImageFont.load_default() else 10
        char_height = 12 if font == ImageFont.load_default() else 14
        
        return (len(text) * char_width, char_height)
    
    def _get_thumbnail_timestamp(self, index: int, intervals: Optional[List[GifInterval]]) -> str:
        """Calculate timestamp for thumbnail based on interval or index"""
        if intervals and index < len(intervals):
            # Use actual interval start time
            start_time = intervals[index].start_time
            return self._format_duration(start_time)
        else:
            # Fallback: estimate timestamp based on index (for cases without intervals)
            # This assumes equal spacing - you may want to adjust this logic
            estimated_time = index * 10.0  # Assume 10 seconds between thumbnails
            return self._format_duration(estimated_time)
        
    def _format_duration(self, seconds: float) -> str:
        """Format seconds to readable duration"""
        h, m, s = int(seconds//3600), int((seconds%3600)//60), int(seconds%60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def _format_file_size(self, bytes_size: int) -> str:
        """Format bytes to readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    def _error_result(self, message: str, start_time: float) -> GifResult:
        """Create error result"""
        return GifResult(
            success=False, 
            gif_files=[], 
            thumbnail_files=[], 
            total_duration=0.0,
            error_message=message, 
            processing_time=time.time() - start_time
        )
    
    def _calculate_grid_layout(self, thumb_files: List[str], grid_size: int, 
                         options: Optional[AutoGifOptions] = None) -> Dict[str, int]:
        """Calculate optimal grid layout with resolution control"""
        num_files = len(thumb_files)
        
        # Calculate grid dimensions
        cols = min(grid_size, num_files)
        rows = (num_files + cols - 1) // cols
        
        # ✅ NEW: Use option-specified thumbnail dimensions or defaults
        if options:
            thumb_width = options.grid_thumb_width
            thumb_height = options.grid_thumb_height
        else:
            # Default thumbnail dimensions
            thumb_width = 160
            thumb_height = 90
        
        return {
            'cols': cols,
            'rows': rows,
            'thumb_width': thumb_width,
            'thumb_height': thumb_height
        }

# Convenience functions
def create_gif_clips(source_file: str, total_duration: float, num_clips: int,
                    clip_duration: float, output_name: str = "clip", **kwargs) -> GifResult:
    """Legacy function for backward compatibility (traditional workflow)"""
    converter = VideoGifConverter()
    interval_step = total_duration / num_clips
    intervals = [(i * interval_step, min((i * interval_step) + clip_duration, total_duration))
                for i in range(num_clips)]
    return converter.create_gif_from_intervals(source_file, intervals, output_name, **kwargs)


def create_auto_gif_clips(source_file: str, num_clips: int, gif_duration: float, 
                         time_gap: float, output_name: str = "auto_clip", **kwargs) -> GifResult:
    """Enhanced auto-generation with time gaps (NEW video-first workflow)"""
    converter = VideoGifConverter()
    options = AutoGifOptions(
        source_file=source_file, num_clips=num_clips, gif_duration=gif_duration,
        time_gap=time_gap, output_name=output_name, **kwargs
    )
    return converter.create_auto_generated_clips(options)

def create_one_click_gif(source_file: str, output_name: str = "oneclick") -> GifResult:
    """
    One-click video to GIF conversion with automatic optimal settings
    
    Args:
        source_file: Path to source video
        output_name: Base name for output files
        
    Returns:
        GifResult with final GIF and thumbnail grid
    """
    converter = VideoGifConverter()
    return converter.create_one_click_gif(source_file, output_name)
