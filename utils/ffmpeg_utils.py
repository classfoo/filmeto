"""
FFmpeg utilities module for video processing operations.
Provides methods for checking/installing ffmpeg, extracting frames,
merging videos, and creating videos from images.
"""
import asyncio
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is installed and available in the system.
    
    Returns:
        bool: True if ffmpeg is available, False otherwise.
    """
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_ffprobe() -> bool:
    """
    Check if ffprobe is installed and available in the system.
    
    Returns:
        bool: True if ffprobe is available, False otherwise.
    """
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False


async def install_ffmpeg() -> bool:
    """
    Install ffmpeg based on the operating system.
    This may require user permissions and internet connection.
    
    Returns:
        bool: True if installation succeeds, False otherwise.
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # On Windows, we can provide instructions or use chocolatey/winget
            logger.info("Please install ffmpeg on Windows using:")
            logger.info("- Chocolatey: choco install ffmpeg")
            logger.info("- Or download from: https://ffmpeg.org/download.html")
            return False  # Manual installation required
            
        elif system == "darwin":  # macOS
            # Try to install using Homebrew
            result = await run_command(['brew', '--version'])
            if result.returncode == 0:
                logger.info("Installing ffmpeg using Homebrew...")
                install_result = await run_command(['brew', 'install', 'ffmpeg'])
                return install_result.returncode == 0
            else:
                logger.info("Please install Homebrew first, then run: brew install ffmpeg")
                return False
                
        elif system == "linux":
            # Try different package managers
            package_managers = [
                (['apt-get', '--version'], ['sudo', 'apt-get', 'install', '-y', 'ffmpeg']),
                (['yum', '--version'], ['sudo', 'yum', 'install', '-y', 'ffmpeg']),
                (['dnf', '--version'], ['sudo', 'dnf', 'install', '-y', 'ffmpeg']),
                (['pacman', '--version'], ['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'])
            ]
            
            for check_cmd, install_cmd in package_managers:
                result = await run_command(check_cmd)
                if result.returncode == 0:
                    logger.info(f"Installing ffmpeg using package manager...")
                    install_result = await run_command(install_cmd)
                    return install_result.returncode == 0
            
            logger.info("Please install ffmpeg using your system's package manager")
            return False
        else:
            logger.warning(f"Unsupported system: {system}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing ffmpeg: {e}")
        return False


async def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    """
    Run a command asynchronously using subprocess.
    
    Args:
        cmd: Command to run as a list of strings
        
    Returns:
        CompletedProcess: Result of the command execution
    """
    # On Unix systems, we can use asyncio.create_subprocess_exec
    if hasattr(asyncio, 'create_subprocess_exec') and platform.system() != "Windows":
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(
            cmd, process.returncode, stdout, stderr
        )
    else:
        # Fallback to synchronous execution for Windows and other systems
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


async def extract_first_frame(video_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Extract the first frame of a video and save it as an image.
    
    Args:
        video_path: Path to the input video file
        output_path: Path where the extracted frame will be saved
        
    Returns:
        bool: True if extraction succeeds, False otherwise
    """
    if not check_ffmpeg():
        logger.error("FFmpeg is not available. Please install it first.")
        return False
        
    try:
        cmd = [
            'ffmpeg',
            '-i', str(video_path),  # input video
            '-vframes', '1',        # extract only the first frame
            '-y',                   # overwrite output file if it exists
            str(output_path)        # output image
        ]
        
        result = await run_command(cmd)
        
        if result.returncode == 0:
            logger.info(f"First frame extracted successfully: {output_path}")
            return True
        else:
            logger.error(f"Error extracting first frame: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Exception occurred while extracting first frame: {e}")
        return False


async def extract_last_frame(video_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Extract the last frame of a video and save it as an image.
    This implementation uses a two-pass approach to get the duration first.
    
    Args:
        video_path: Path to the input video file
        output_path: Path where the extracted frame will be saved
        
    Returns:
        bool: True if extraction succeeds, False otherwise
    """
    if not check_ffmpeg():
        logger.error("FFmpeg is not available. Please install it first.")
        return False
        
    try:
        # First, try to get the duration of the video using ffprobe
        cmd_duration = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'csv=p=0',
            '-show_entries', 'format=duration',
            str(video_path)
        ]
        
        try:
            result_duration = await run_command(cmd_duration)
            duration_extraction_success = result_duration.returncode == 0
        except Exception:
            # If ffprobe is not available or fails, set flag to False
            result_duration = None
            duration_extraction_success = False
        
        if not duration_extraction_success:
            logger.warning("ffprobe not available or failed, using alternative approach with -sseof")
            # Try alternative approach: go to the end of the video and extract a frame
            cmd = [
                'ffmpeg',
                '-sseof', '-1',  # seek to 1 second before the end
                '-i', str(video_path),
                '-vframes:v', '1',
                '-update', '1',
                '-y',
                str(output_path)
            ]
        else:
            # Parse duration to get the last frame
            duration_str = result_duration.stdout.decode().strip()
            try:
                duration = float(duration_str)
                # Use the exact duration to seek to the end
                cmd = [
                    'ffmpeg',
                    '-ss', str(max(0, duration - 0.1)),  # seek to very end (minus small buffer)
                    '-i', str(video_path),
                    '-vframes:v', '1',
                    '-y',
                    str(output_path)
                ]
            except ValueError:
                # If parsing fails, use the alternative approach
                cmd = [
                    'ffmpeg',
                    '-sseof', '-1',  # seek to 1 second before the end
                    '-i', str(video_path),
                    '-vframes:v', '1',
                    '-update', '1',
                    '-y',
                    str(output_path)
                ]
        
        result = await run_command(cmd)
        
        if result.returncode == 0:
            logger.info(f"Last frame extracted successfully: {output_path}")
            return True
        else:
            logger.error(f"Error extracting last frame: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Exception occurred while extracting last frame: {e}")
        return False


async def merge_videos(video_paths: List[Union[str, Path]], output_path: Union[str, Path], 
                      codec: str = 'copy') -> bool:
    """
    Merge a batch of video files into a single video file.
    
    Args:
        video_paths: List of paths to video files to be merged
        output_path: Path where the merged video will be saved
        codec: Video codec to use ('copy' to copy streams without re-encoding, 
               or specify encoding like 'libx264')
               
    Returns:
        bool: True if merging succeeds, False otherwise
    """
    if not check_ffmpeg():
        logger.error("FFmpeg is not available. Please install it first.")
        return False
        
    if len(video_paths) < 1:
        logger.error("At least one video file is required for merging.")
        return False
        
    # Validate that all video files exist
    for path in video_paths:
        if not os.path.exists(path):
            logger.error(f"Video file does not exist: {path}")
            return False
    
    try:
        # Create a temporary file listing all videos to be merged
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            for video_path in video_paths:
                # Properly escape paths for ffmpeg
                temp_file.write(f"file '{os.path.abspath(video_path)}'\n")
            temp_list_path = temp_file.name
        
        # Prepare the command based on codec
        if codec == 'copy':
            # Use concat demuxer which is faster but requires compatible formats
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',  # Allow absolute paths
                '-i', temp_list_path,
                '-c', 'copy',  # Copy streams without re-encoding
                '-y',  # Overwrite output file
                str(output_path)
            ]
        else:
            # Re-encode the video with specified codec
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_list_path,
                '-c:v', codec,  # Video codec
                '-c:a', 'copy',  # Copy audio as-is (or use codec for audio too)
                '-y',
                str(output_path)
            ]
        
        result = await run_command(cmd)
        
        # Clean up temporary file
        os.unlink(temp_list_path)
        
        if result.returncode == 0:
            logger.info(f"Videos merged successfully: {output_path}")
            return True
        else:
            logger.error(f"Error merging videos: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Exception occurred while merging videos: {e}")
        # Clean up temporary file if it exists
        if 'temp_list_path' in locals():
            try:
                os.unlink(temp_list_path)
            except:
                pass
        return False


async def images_to_video(image_paths: List[Union[str, Path]], 
                         output_path: Union[str, Path], 
                         duration_per_image: float = 1.0,
                         fps: int = 30,
                         codec: str = 'libx264') -> bool:
    """
    Convert a batch of images to a video with specified duration.
    
    Args:
        image_paths: List of paths to image files
        output_path: Path where the output video will be saved
        duration_per_image: Duration (in seconds) each image should be displayed
        fps: Frames per second for the output video
        codec: Video codec to use (default: libx264)
        
    Returns:
        bool: True if conversion succeeds, False otherwise
    """
    if not check_ffmpeg():
        logger.error("FFmpeg is not available. Please install it first.")
        return False
        
    if len(image_paths) < 1:
        logger.error("At least one image file is required.")
        return False
        
    # Validate that all image files exist
    for path in image_paths:
        if not os.path.exists(path):
            logger.error(f"Image file does not exist: {path}")
            return False
    
    try:
        # Calculate total duration
        total_duration = len(image_paths) * duration_per_image
        
        # Create a temporary file with image list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            for image_path in image_paths:
                # Use the "ffconcat" protocol to specify duration for each image
                temp_file.write(f"file '{os.path.abspath(image_path)}'\n")
                temp_file.write(f"duration {duration_per_image}\n")
            temp_list_path = temp_file.name
        
        # For image sequences with specified durations, use the concat demuxer
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list_path,
            '-c:v', codec,  # Video codec
            '-r', str(fps),  # FPS
            '-pix_fmt', 'yuv420p',  # Pixel format for better compatibility
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        result = await run_command(cmd)
        
        # Clean up temporary file
        os.unlink(temp_list_path)
        
        if result.returncode == 0:
            logger.info(f"Images converted to video successfully: {output_path} "
                       f"(Duration: {total_duration}s, FPS: {fps})")
            return True
        else:
            logger.error(f"Error converting images to video: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Exception occurred while converting images to video: {e}")
        # Clean up temporary file if it exists
        if 'temp_list_path' in locals():
            try:
                os.unlink(temp_list_path)
            except:
                pass
        return False


# Additional utility function to validate ffmpeg and ffprobe availability with installation option
async def ensure_ffmpeg() -> bool:
    """
    Ensure ffmpeg is available (primary requirement), with optional ffprobe availability.
    The function ensures ffmpeg is available (installing if necessary) and logs ffprobe status.
    Many operations can work with just ffmpeg, but some functions may need ffprobe as well.
    
    Returns:
        bool: True if ffmpeg is available (main requirement), False if ffmpeg is not available
    """
    ffmpeg_available = check_ffmpeg()
    ffprobe_available = check_ffprobe()
    
    if ffmpeg_available and ffprobe_available:
        logger.info("Both FFmpeg and FFprobe are already available.")
        return True
    elif ffmpeg_available and not ffprobe_available:
        logger.info("FFmpeg is available but FFprobe is not. FFmpeg is the main requirement.")
        logger.warning("FFprobe is not available but is not critical for most operations.")
        return True
    elif not ffmpeg_available:
        logger.info("FFmpeg not found. Attempting to install...")
        if await install_ffmpeg():
            if check_ffmpeg():
                logger.info("FFmpeg installation successful.")
                ffmpeg_available = True
                # After installing ffmpeg, check again for ffprobe
                ffprobe_available = check_ffprobe()
                if ffprobe_available:
                    logger.info("FFprobe is also available after FFmpeg installation.")
                else:
                    logger.warning("FFmpeg installed but FFprobe is not available. This is okay for most operations.")
                return True
            else:
                logger.error("FFmpeg installation appeared to succeed but is not available.")
                return False
        else:
            logger.error("FFmpeg installation failed.")
            return False