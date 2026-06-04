# yt-dlp Command Templates
import os

DEFAULT_FLAGS = [
    "--no-abort-on-error",
    "--retries", "infinite",
    "--fragment-retries", "infinite"
]

PLAYLIST_FLAGS = [
    "--ignore-errors",
]

SUPPORTED_BROWSERS = [
    "default",
    "firefox", 
    "chrome", 
    "edge", 
    "opera", 
    "brave", 
    "vivaldi", 
    "safari", 
    "Flatpak",
    "Custom File"
]

QUALITY_TEMPLATES = {
    "best": {
        "format": "bv*+ba/b",
        "merge_format": "mkv",
        "description": "Best Quality (4K/2K/HD)"
    },
    "compatible": {
        "format": "bestvideo[height<=720]+bestaudio[ext=m4a]/bv*[height<=720]+ba/b",
        "merge_format": "mp4",
        "description": "Compatible (MP4 720p - All Devices)"
    },
    "sd_480": {
        "format": "bestvideo[height<=480]+bestaudio[ext=m4a]/bv*[height<=480]+ba/b",
        "merge_format": "mp4",
        "description": "SD 480p (MP4 - All Devices)"
    },
    "hd_1080": {
        "format": "bestvideo[height<=1080]+bestaudio[ext=m4a]/bv*[height<=1080]+ba/b",
        "merge_format": "mp4",
        "description": "HD 1080p (MP4 - Most Devices)"
    },
    "best_audio_mp3": {
        "format": "bestaudio/best",
        "extract_audio": True,
        "audio_format": "mp3",
        "audio_quality": "0",
        "description": "Best MP3 Audio (High Quality)"
    },
    "audio_mp3": {
        "format": "bestaudio/best",
        "extract_audio": True,
        "audio_format": "mp3",
        "audio_quality": "0",
        "description": "Compatible Audio (MP3 - All Devices)"
    },
    "audio_m4a": {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "extract_audio": True,
        "audio_format": "m4a",
        "audio_quality": "0",
        "description": "Universal Audio (M4A/AAC - All Devices)"
    },
    "video_no_audio": {
        "format": "bestvideo[ext=mp4]/bestvideo",
        "description": "Video - No Audio"
    }
}

OUTPUT_TEMPLATE = "%(playlist_title)s/%(title)s.%(ext)s"  # playlist subfolder set in build_command

AUDIO_EXTS = {"mp3", "m4a", "aac", "flac", "wav", "opus", "ogg"}
VIDEO_EXTS = {"mp4", "mkv", "webm", "avi", "mov", "wmv", "flv"}

SUBFOLDERS = {
    "audio": "Audio",
    "video": "Videos",
    "file": "Files",
}

def get_subfolder(filename, mode=None):
    if mode and mode in ("best_audio_mp3", "audio_mp3", "audio_m4a"):
        return SUBFOLDERS["audio"]
    if mode and mode in QUALITY_TEMPLATES:
        return SUBFOLDERS["video"]
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext in AUDIO_EXTS:
        return SUBFOLDERS["audio"]
    if ext in VIDEO_EXTS:
        return SUBFOLDERS["video"]
    return SUBFOLDERS["file"]
