import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage
import os
import re
import json
import subprocess
import glob
import threading
import sys
import time
import traceback

from datetime import datetime
from PIL import Image
import arabic_reshaper
from bidi.algorithm import get_display
from downloader import YtDownloader, DirectDownloader, is_direct_url
from download_manager import DownloadManager
from api_server import APIServer
from config import QUALITY_TEMPLATES

DARK_COLORS = {
    "bg": "#09090b",
    "surface": "#18181b",
    "card": "#27272a",
    "card_hover": "#3f3f46",
    "border": "#3f3f46",
    "border_light": "#52525b",
    "primary": "#10b981",
    "primary_hover": "#059669",
    "primary_light": "#34d399",
    "primary_gradient_from": "#059669",
    "primary_gradient_to": "#34d399",
    "success": "#10b981",
    "success_bg": "#064e3b",
    "success_hover": "#059669",
    "error": "#ef4444",
    "error_bg": "#450a0a",
    "error_hover": "#dc2626",
    "warning": "#f59e0b",
    "warning_hover": "#d97706",
    "text": "#f4f4f5",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "text_heading": "#ffffff",
    "input_bg": "#18181b",
    "input_border": "#3f3f46",
    "progress_bg": "#064e3b",
    "progress_fill": "#10b981",
}

LIGHT_COLORS = {
    "bg": "#f4f4f5",
    "surface": "#ffffff",
    "card": "#ffffff",
    "card_hover": "#e4e4e7",
    "border": "#d4d4d8",
    "border_light": "#a1a1aa",
    "primary": "#10b981",
    "primary_hover": "#059669",
    "primary_light": "#34d399",
    "primary_gradient_from": "#059669",
    "primary_gradient_to": "#34d399",
    "success": "#10b981",
    "success_bg": "#d1fae5",
    "success_hover": "#059669",
    "error": "#ef4444",
    "error_bg": "#fecaca",
    "error_hover": "#dc2626",
    "warning": "#f59e0b",
    "warning_hover": "#d97706",
    "text": "#18181b",
    "text_secondary": "#52525b",
    "text_muted": "#71717a",
    "text_heading": "#09090b",
    "input_bg": "#f4f4f5",
    "input_border": "#d4d4d8",
    "progress_bg": "#d1fae5",
    "progress_fill": "#10b981",
}

COLORS = DARK_COLORS

FONTS = {
    "heading": {"size": 28, "weight": "bold"},
    "subheading": {"size": 17, "weight": "bold"},
    "body": {"size": 15},
    "body_bold": {"size": 15, "weight": "bold"},
    "small": {"size": 13},
    "icon": {"size": 22},
    "icon_large": {"size": 28},
}

_font_cache = {}
def get_font(key, lang="English"):
    cache_key = (key, lang)
    if cache_key not in _font_cache:
        cfg = FONTS.get(key, FONTS["body"]).copy()
        if lang == "Arabic":
            cfg["family"] = "Noto Naskh Arabic"
        _font_cache[cache_key] = ctk.CTkFont(**cfg)
    return _font_cache[cache_key]


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_ARABIC_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')

def _contains_arabic(text):
    return bool(_ARABIC_RE.search(text))

def fix_text(text, lang="Arabic"):
    if not text: return ""
    if lang == "Arabic" or _contains_arabic(text):
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except Exception:
            return text
    return text

ICONS = {
    "settings": "⚙️",
    "link": "🔗",
    "paste": "📋",
    "folder": "📂",
    "download": "⬇️",
    "cancel": "✖",
    "success": "✔️",
    "error": "❌",
    "info": "ℹ️",
    "music": "🎵",
    "video": "🎬",
    "playlist": "📑",
    "globe": "🌐",
    "check": "✅",
    "settings_gear": "⚙️",
    "user": "👤",
    "speed": "⚡",
    "size": "📦",
    "time": "⏱️",
    "star": "⭐",
    "pencil": "✏️",
    "play": "▶️",
    "refresh": "🔄",
    "guide": "📖",
}

GUIDE_TEXT = """\
Required Packages for Boussari Download
========================================

This application runs as a Flatpak on Linux and requires
the following packages to function correctly.

1. GNOME Platform Runtime (org.gnome.Platform//50)
   - Size: ~1.1 GB
   - Provides the graphical interface environment (GTK,
     Python, Tcl/Tk and system libraries).
   - Downloaded once and shared across all Flatpak apps.

2. FFmpeg Extension (org.freedesktop.Platform.ffmpeg-full)
   - Size: ~50 MB
   - Required for merging audio and video streams in
     yt-dlp. Without it, format selection may fail.
   - Follows the same branch as your runtime (e.g. 24.08).

3. yt-dlp (bundled inside the app)
   - Included in the Flatpak package itself.
   - No additional installation needed.

Installation via Flathub (Recommended)
---------------------------------------
Simply run:
   flatpak install flathub com.boussari.downloader

All dependencies (runtime + ffmpeg) are resolved and
downloaded automatically by Flatpak.

Manual Installation from .flatpak Bundle
-----------------------------------------
If you have the bundle file, install in this order:

   1. Install the runtime:
      flatpak install flathub org.gnome.Platform//50

   2. Install the ffmpeg extension:
      flatpak install flathub \\
        org.freedesktop.Platform.ffmpeg-full//24.08

   3. Install the app bundle:
      flatpak install --user BoussariDownload.flatpak

Network Requirements
---------------------
- A working internet connection is required for
  downloading videos from YouTube or other sites.
- The app uses yt-dlp which downloads media data
  directly from streaming platforms.

Notes
-----
- The runtime and ffmpeg extension are large downloads
  (1.1 GB + 50 MB) but only need to be downloaded once.
- All Flatpak data is sandboxed for security.
- Downloads are saved to your Downloads/Videos folder
  by default, organised into subfolders.
"""

TRANSLATIONS = {
    "Arabic": {
        "settings": "\u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A",
        "url_label": "\u0631\u0627\u0628\u0637 \u0627\u0644\u0641\u064A\u062F\u064A\u0648 / \u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u062A\u0634\u063A\u064A\u0644",
        "paste": "\u0644\u0635\u0642",
        "playlist_check": "\u062A\u062D\u0645\u064A\u0644 \u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u062A\u0634\u063A\u064A\u0644 \u0643\u0627\u0645\u0644\u0629",
        "storage_label": "\u0645\u0648\u0642\u0639 \u0627\u0644\u062D\u0641\u0638",
        "browse": "\u062A\u0635\u0641\u062D",
        "quality_label": "\u062C\u0648\u062F\u0629 \u0627\u0644\u062A\u062D\u0645\u064A\u0644",
        "cookies_label": "\u0645\u0635\u062F\u0631 \u0627\u0644\u0643\u0648\u0643\u064A\u0632",
        "lang_label": "\u0627\u0644\u0644\u063A\u0629",
        "about": "\u062D\u0648\u0644 \u0627\u0644\u062A\u0637\u0628\u064A\u0642",
        "guide": "\u062F\u0644\u064A\u0644 \u0627\u0644\u062A\u062B\u0628\u064A\u062A",
        "guide_title": "\u062F\u0644\u064A\u0644 \u0627\u0644\u062D\u0632\u0645 \u0627\u0644\u0645\u0637\u0644\u0648\u0628\u0629",
        "theme_label": "\u0627\u0644\u0645\u0638\u0647\u0631",
        "start_btn": "\u0627\u0628\u062F\u0623 \u0627\u0644\u062A\u062D\u0645\u064A\u0644",
        "cancel_btn": "\u0625\u0644\u063A\u0627\u0621 \u0627\u0644\u062A\u062D\u0645\u064A\u0644",
        "cancelling": "\u062C\u0627\u0631\u064A \u0627\u0644\u0625\u0644\u063A\u0627\u0621...",
        "success_title": "\u0646\u062C\u0627\u062D",
        "success_msg": "\u062A\u0645 \u0627\u0644\u062A\u062D\u0645\u064A\u0644 \u0628\u0646\u062C\u0627\u062D!",
        "error_title": "\u062E\u0637\u0623",
        "error_msg": "\u0641\u0634\u0644 \u0627\u0644\u062A\u062D\u0645\u064A\u0644. \u064A\u0631\u062C\u0649 \u0645\u0631\u0627\u062C\u0639\u0629 \u0627\u0644\u0633\u062C\u0644\u0627\u062A.",
        "cancelled_title": "\u062A\u0645 \u0627\u0644\u0625\u0644\u063A\u0627\u0621",
        "cancelled_msg": "\u062A\u0645 \u0625\u0644\u063A\u0627\u0621 \u0627\u0644\u062A\u062D\u0645\u064A\u0644 \u0628\u0648\u0627\u0633\u0637\u0629 \u0627\u0644\u0645\u0633\u062A\u062E\u062F\u0645.",
        "exception_title": "\u0627\u0633\u062A\u062B\u0646\u0627\u0621",
        "no_playlist": "\u0644\u0627 \u062A\u0648\u062C\u062F \u0642\u0627\u0626\u0645\u0629 \u0646\u0634\u0637\u0629",
        "video_of": "\u0641\u064A\u062F\u064A\u0648 {index} \u0645\u0646 {total}",
        "audio_of": "\u0645\u0644\u0641 \u0635\u0648\u062A\u064A {index} \u0645\u0646 {total}",
        "size": "\u0627\u0644\u062D\u062C\u0645",
        "speed": "\u0627\u0644\u0633\u0631\u0639\u0629",
        "eta": "\u0627\u0644\u0648\u0642\u062A \u0627\u0644\u0645\u062A\u0628\u0642\u064A",
        "remaining": "\u0627\u0644\u0645\u062A\u0628\u0642\u064A",
        "dev_info": "The application was provided by Ahmed Boussari, focusing on simplifying technical and programming use in a step to make the Linux world better. Ahmed Boussari is a Moroccan youth who loves computer programming and everything related to technology, always aiming to achieve the best results in the simplest possible ways.",
        "version": "\u0627\u0644\u0625\u0635\u062F\u0627\u0631: 2.3.7",
        "close": "\u0625\u063A\u0644\u0627\u0642",
        "open_folder": "\u0641\u062A\u062D \u0627\u0644\u0645\u062C\u0644\u062F",
        "add_download": "\u0625\u0636\u0627\u0641\u0629 \u062A\u062D\u0645\u064A\u0644",
        "pause": "\u0625\u064A\u0642\u0627\u0641 \u0645\u0624\u0642\u062A",
        "resume": "\u0627\u0633\u062A\u0626\u0646\u0627\u0641",
        "retry": "\u0625\u0639\u0627\u062F\u0629 \u0627\u0644\u0645\u062D\u0627\u0648\u0644\u0629",
        "exit": "\u062E\u0631\u0648\u062C",
        "queued": "\u0641\u064A \u0627\u0644\u0627\u0646\u062A\u0638\u0627\u0631",
        "downloading": "\u062C\u0627\u0631\u064A \u0627\u0644\u062A\u062D\u0645\u064A\u0644",
        "completed": "\u062A\u0645 \u0627\u0644\u062A\u062D\u0645\u064A\u0644",
        "existing": "\u0645\u0648\u062C\u0648\u062F \u0645\u0633\u0628\u0642\u0627\u064B",
        "clear_history": "\u062D\u0630\u0641 \u0627\u0644\u0633\u062C\u0644",
        "confirm_title": "\u062A\u0623\u0643\u064A\u062F",
        "clear_history_confirm": "\u0647\u0644 \u0623\u0646\u062A \u0645\u062A\u0623\u0643\u062F \u0645\u0646 \u062D\u0630\u0641 \u0627\u0644\u0633\u062C\u0644 \u0628\u0627\u0644\u0643\u0645\u0644\u061F",
        "clear_history_success": "\u062A\u0645 \u062D\u0630\u0641 \u0627\u0644\u0633\u062C\u0644 \u0646\u062C\u0627\u062D\u0627!",
        "clear_history_error": "\u062E\u0637\u0623 \u0623\u062A\u0646\u0627 \u062D\u0630\u0641 \u0627\u0644\u0633\u062C\u0644.",
        "enter_url_first": "\u064A\u0631\u062C\u0649 \u0625\u062F\u062E\u0627\u0644 \u0627\u0644\u0631\u0627\u0628\u0637 \u0623\u0648\u0644\u0627\u064B!",
    },
    "English": {
        "settings": "Settings",
        "url_label": "Video / Playlist URL",
        "paste": "Paste",
        "playlist_check": "Download entire playlist",
        "storage_label": "Download Location",
        "browse": "Browse",
        "quality_label": "Quality Mode",
        "cookies_label": "Cookies Source",
        "lang_label": "Language",
        "about": "About App",
        "guide": "Guide",
        "guide_title": "Required Packages Guide",
        "theme_label": "Theme",
        "start_btn": "START DOWNLOAD",
        "cancel_btn": "CANCEL DOWNLOAD",
        "cancelling": "Cancelling...",
        "success_title": "Success",
        "success_msg": "Download completed successfully!",
        "error_title": "Error",
        "confirm_title": "Confirm",
        "error_msg": "Download failed. Check logs.",
        "cancelled_title": "Cancelled",
        "enter_url_first": "Please enter a URL first!",
        "cancelled_msg": "Download was cancelled by user.",
        "exception_title": "Exception",
        "no_playlist": "No active playlist",
        "video_of": "Video {index} of {total}",
        "audio_of": "Audio {index} of {total}",
        "size": "Size",
        "speed": "Speed",
        "eta": "ETA",
        "remaining": "Remaining",
        "dev_info": "The application was provided by Ahmed Boussari, focusing on simplifying technical and programming use in a step to make the Linux world better. Ahmed Boussari is a Moroccan youth who loves computer programming and everything related to technology, always aiming to achieve the best results in the simplest possible ways.",
        "version": "Version: 2.3.7",
        "close": "Close",
        "open_folder": "Open Folder",
        "add_download": "ADD DOWNLOAD",
        "pause": "Pause",
        "resume": "Resume",
        "retry": "Retry",
        "exit": "Exit",
        "queued": "Queued",
        "downloading": "Downloading",
        "completed": "Downloaded",
        "existing": "Already exists",
        "clear_history": "Clear History",
        "clear_history_confirm": "Are you sure you want to clear the entire history?",
        "clear_history_success": "History cleared successfully!",
        "clear_history_error": "Error clearing history.",
    }
}


def make_card(parent, **kwargs):
    kwargs.setdefault("fg_color", COLORS["card"])
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", COLORS["border"])
    kwargs.setdefault("corner_radius", 20)
    return ctk.CTkFrame(parent, **kwargs)


def make_icon_label(parent, icon, text, lang="Arabic", **kwargs):
    labeled_text = f"{icon}  {fix_text(text, lang)}"
    kwargs.setdefault("font", get_font("body", lang))
    kwargs.setdefault("text_color", COLORS["text_secondary"])
    return ctk.CTkLabel(parent, text=labeled_text, **kwargs)

_app_ref = None


class DownloadItem(ctk.CTkFrame):
    def __init__(self, master, title, extension, index=None, total=None, file_path=None, url=None, lang="Arabic", is_history=False):
        super().__init__(
            master,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=20,
            height=155
        )
        self.is_history = is_history
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self._file_path = file_path
        self._url = url
        self._state = "queued"
        self._last_percent = 0.0
        self._title = title
        self._lang = lang
        self._ext = extension

        is_rtl = lang == "Arabic"

        type_icon = ICONS["music"] if extension in ("mp3", "m4a", "aac", "flac", "wav", "opus") else ICONS["video"]

        if index and total:
            text = TRANSLATIONS[lang]["video_of"].format(index=index, total=total)
            self.index_label = ctk.CTkLabel(
                self, text=f"{type_icon}  {fix_text(text, lang)}",
                font=get_font("body_bold", lang),
                text_color=COLORS["primary_light"]
            )
            self.index_label.grid(row=0, column=0, padx=16, pady=(14, 0), sticky="e" if is_rtl else "w")

        title_text = f"{ICONS['pencil']} {title}"
        self.title_label = ctk.CTkLabel(
            self, text=fix_text(title_text, lang),
            font=get_font("body_bold", lang),
            anchor="e" if is_rtl else "w", text_color=COLORS["text"],
            wraplength=380
        )
        self.title_label.grid(row=0 if not (index and total) else 1, column=0,
                               padx=16, pady=(16 if not (index and total) else 4, 4), sticky="ew")

        pbar_row = (1 if not (index and total) else 2)
        self.pbar_container = ctk.CTkFrame(self, fg_color="transparent")
        self.pbar_container.grid(row=pbar_row, column=0, padx=16, pady=(6, 0), sticky="ew")
        self.pbar_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            self.pbar_container, height=10, corner_radius=5,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["progress_fill"],
            mode="determinate"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", expand=True)
        self._last_ui_update = 0

        stats_row = pbar_row + 1
        actions_row = stats_row + 1

        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=26)
        self.stats_frame.grid(row=stats_row, column=0, padx=16, pady=(2, 0), sticky="ew")
        self.stats_frame.grid_columnconfigure(0, weight=1)

        self.ext_label = ctk.CTkLabel(
            self.stats_frame,
            text=f"{type_icon} . . .",
            font=get_font("body_bold", lang),
            text_color=COLORS["primary_light"]
        )
        self.ext_label.pack(side="left" if not is_rtl else "right", padx=(4, 6), pady=2)

        self.size_label = ctk.CTkLabel(
            self.stats_frame,
            text=f"{ICONS['size']} 0 MB",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["primary_light"]
        )
        self.size_label.pack(side="left" if not is_rtl else "right", padx=3, pady=2)

        self.speed_label = ctk.CTkLabel(
            self.stats_frame,
            text=f"{ICONS['speed']} 0 KB/s",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["success"]
        )
        self.speed_label.pack(side="left" if not is_rtl else "right", padx=3, pady=2)

        self.percent_label = ctk.CTkLabel(
            self.stats_frame,
            text="0.0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        )
        self.percent_label.pack(side="left" if not is_rtl else "right", padx=3, pady=2)

        self.eta_label = ctk.CTkLabel(
            self.stats_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["warning"]
        )
        self.eta_label.pack(side="left" if not is_rtl else "right", padx=3, pady=2)

        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=32)
        self.actions_frame.grid(row=actions_row, column=0, padx=16, pady=(2, 12), sticky="ew")
        self.actions_frame.grid_columnconfigure(0, weight=1)

        self.state_label = ctk.CTkLabel(
            self.actions_frame,
            text="",
            font=get_font("body_bold", lang),
            text_color=COLORS["warning"]
        )
        self.state_label.pack(side="left", padx=(0, 6), pady=2)

        self.actions_buttons = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        self.actions_buttons.pack(side="right", pady=2)

        self.open_btn = ctk.CTkButton(
            self.actions_buttons,
            text=ICONS["folder"],
            width=34, height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text"],
            font=get_font("body", lang),
            command=self._open_file
        )

        self.pause_btn = ctk.CTkButton(
            self.actions_buttons,
            text=ICONS["time"],
            width=34, height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["warning"],
            font=get_font("body", lang),
            command=self._on_pause_click
        )
        self.pause_btn.pack(side="left", padx=2)
        self.pause_btn.pack_forget()

        self.resume_btn = ctk.CTkButton(
            self.actions_buttons,
            text=ICONS["play"],
            width=34, height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["success"],
            font=get_font("body", lang),
            command=self._on_resume_click
        )
        self.resume_btn.pack(side="left", padx=2)
        self.resume_btn.pack_forget()

        self.retry_btn = ctk.CTkButton(
            self.actions_buttons,
            text=ICONS["refresh"],
            width=34, height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["primary"],
            font=get_font("body", lang),
            command=self._on_retry_click
        )
        self.retry_btn.pack(side="left", padx=2)
        self.retry_btn.pack_forget()

        self.cancel_btn = ctk.CTkButton(
            self.actions_buttons,
            text=ICONS["cancel"],
            width=34, height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["error"],
            font=get_font("body", lang),
            command=self._on_cancel_click
        )
        self.cancel_btn.pack(side="left", padx=2)
        self.cancel_btn.pack_forget()

        self.on_pause = None
        self.on_resume = None
        self.on_retry = None
        self.on_cancel = None
        self.on_completed = None


    def _open_file(self):
        if not self._file_path:
            return
        if not os.path.exists(self._file_path):
            print(f"[Open] File not found: {self._file_path}")
            return
        try:
            subprocess.Popen(['xdg-open', self._file_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("[Open] xdg-open not found. Install xdg-utils.")
        except Exception as e:
            print(f"[Open] Error: {e}")

    def _on_pause_click(self):
        if self.on_pause:
            self.on_pause(self._title)

    def _on_resume_click(self):
        if self.on_resume:
            self.on_resume(self._title)

    def _on_retry_click(self):
        if self.on_retry:
            self.on_retry(self._title)

    def _on_cancel_click(self):
        if self.on_cancel:
            self.on_cancel(self._title)

    def set_file_path(self, path):
        self._file_path = path

    def set_state(self, state):
        self._state = state
        self.open_btn.pack_forget()
        self.pause_btn.pack_forget()
        self.resume_btn.pack_forget()
        self.retry_btn.pack_forget()
        self.cancel_btn.pack_forget()
        lang = self._lang
        if state == "completed":
            if self._file_path:
                self.open_btn.pack(side="right", padx=(2, 0), pady=2)
            if self.on_completed:
                self.on_completed(self._title, self._file_path, self._ext, self._url)
            if getattr(self, '_already_existed', False):
                self.state_label.configure(text=f"{ICONS['check']} {fix_text(TRANSLATIONS[self._lang]['existing'], self._lang)}", text_color=COLORS["warning"])
            else:
                self.state_label.configure(text=f"{ICONS['check']} {fix_text(TRANSLATIONS[self._lang]['completed'], self._lang)}", text_color=COLORS["success"])
        else:
            self.title_label.unbind("<Button-1>")
            self.title_label.configure(cursor="")
        if state == "downloading":
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            self.pause_btn.pack(side="right", padx=2, pady=2)
            self.cancel_btn.pack(side="right", padx=(2, 0), pady=2)
            self.state_label.configure(text=f"{ICONS['download']} {fix_text(TRANSLATIONS[lang]['downloading'], lang)}", text_color=COLORS["warning"])
        elif state == "queued":
            self.cancel_btn.pack(side="right", padx=(2, 0), pady=2)
            self.state_label.configure(text=f"{ICONS['time']} {fix_text(TRANSLATIONS[lang]['queued'], lang)}", text_color=COLORS["primary_light"])
        elif state == "paused":
            self.resume_btn.pack(side="right", padx=2, pady=2)
            self.cancel_btn.pack(side="right", padx=(2, 0), pady=2)
            self.state_label.configure(text=f"{ICONS['time']} {fix_text(TRANSLATIONS[lang]['pause'], lang)}", text_color=COLORS["warning"])
        elif state == "error":
            self.retry_btn.pack(side="right", padx=2, pady=2)
            self.cancel_btn.pack(side="right", padx=(2, 0), pady=2)
            self.state_label.configure(text=f"{ICONS['error']} {fix_text(TRANSLATIONS[lang]['error_title'], lang)}", text_color=COLORS["error"])

    def update_progress(self, percent, speed, extension, size, eta=None):
        try:
            lang = self.winfo_toplevel().language.get()
        except Exception:
            lang = "Arabic"
        try:
            self._last_percent = percent
            self.progress_bar.set(min(percent / 100.0, 1.0))
            type_icon = ICONS["music"] if extension in ("mp3", "m4a", "aac", "flac", "wav", "opus") else ICONS["video"]
            if extension != "unknown":
                self.ext_label.configure(text=f"{type_icon} .{extension}")
            self.size_label.configure(text=f"{ICONS['size']} {size}")
            self.speed_label.configure(text=f"{ICONS['speed']} {speed}")
            self.percent_label.configure(text=f"{percent:.1f}%")
            self.eta_label.configure(text=f"{ICONS['time']} {eta}" if eta else "")
            if percent >= 100 and self._state != "completed":
                self.set_state("completed")
        except Exception:
            pass



class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        super().__init__()
        self.title("Boussari Download")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg"])
        base = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base, "extension", "icons", "icon128.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base, "..", "share", "icons", "hicolor", "128x128", "apps", "com.boussari.downloader.png")
        if os.path.exists(icon_path):
            try:
                self._icon = PhotoImage(file=icon_path)
                self.iconphoto(True, self._icon)
            except Exception:
                pass
        self.settings_file = os.path.join(os.path.expanduser("~/.config/boussari-downloader"), "settings.json")

        self.download_path = ctk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.selected_mode = ctk.StringVar(value="hd_1080")
        self.is_playlist = ctk.BooleanVar(value=True)
        self.cookie_source = ctk.StringVar(value="default")
        self.cookie_path = ctk.StringVar(value="")
        self.flatpak_browser = ctk.StringVar(value="firefox")
        self.open_after_download = ctk.BooleanVar(value=False)
        self.language = ctk.StringVar(value="English")
        self.appearance_mode = ctk.StringVar(value="dark")


        lang = self.language.get()
        self.playlist_status = ctk.StringVar(value=fix_text(TRANSLATIONS[lang]["no_playlist"], lang))

        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        self.history_file = os.path.join(os.path.dirname(self.settings_file), "history.json")
        self._session_file = os.path.join(os.path.dirname(self.settings_file), "session.json")
        self.load_settings()
        self._apply_theme()

        self._lock_file = os.path.join(os.path.dirname(self.settings_file), "app.lock")
        if not self._acquire_lock():
            self.destroy()
            sys.exit(0)

        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())

        self.active_downloads = {}
        self._extension_format = None
        self._dm = DownloadManager()
        self._download_queue = []
        self._active_item_id = None
        self._queue_lock = threading.Lock()
        global _app_ref
        _app_ref = self
        self._start_api_server()
        self._load_history()
        self._restore_session()
        self.after(15000, self._session_timer)

    def _acquire_lock(self):
        try:
            if os.path.exists(self._lock_file):
                with open(self._lock_file) as f:
                    pid = int(f.read().strip())
                try:
                    os.kill(pid, 0)
                    print(f"App already running (PID {pid}). Exiting.")
                    return False
                except (OSError, ProcessLookupError):
                    pass
            with open(self._lock_file, "w") as f:
                f.write(str(os.getpid()))
            return True
        except Exception as e:
            print(f"Lock error: {e}")
            return True

    def _release_lock(self):
        try:
            if os.path.exists(self._lock_file):
                with open(self._lock_file) as f:
                    pid = int(f.read().strip())
                if pid == os.getpid():
                    os.remove(self._lock_file)
        except Exception:
            pass

    def _start_api_server(self):
        self._api = APIServer()
        self._api.start(self)

    def start_download_with_url(self, url, fmt="best"):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        if fmt in QUALITY_TEMPLATES:
            self.selected_mode.set(fmt)
            self._extension_format = None
        elif fmt == "download_all":
            self._extension_format = "download_all"
        else:
            self._extension_format = fmt
        self.start_download_thread()

    def handle_extension_download(self, url, fmt):
        self.after(0, lambda: self.start_download_with_url(url, fmt))

    def get_download_path(self):
        return self.download_path.get()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    self.download_path.set(settings.get("download_path", os.path.expanduser("~/Downloads")))
                    mode = settings.get("selected_mode", "best")
                    if mode not in QUALITY_TEMPLATES:
                        for key, val in QUALITY_TEMPLATES.items():
                            if val["description"] == mode:
                                mode = key
                                break
                        else:
                            mode = "best"
                    self.selected_mode.set(mode)
                    self.is_playlist.set(settings.get("is_playlist", True))
                    self.cookie_source.set(settings.get("cookie_source", "default"))
                    self.cookie_path.set(settings.get("cookie_path", ""))
                    self.flatpak_browser.set(settings.get("flatpak_browser", "firefox"))
                    self.open_after_download.set(settings.get("open_after_download", False))
                    self.language.set(settings.get("language", "English"))
                    self.appearance_mode.set(settings.get("appearance_mode", "dark"))
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        settings = {
            "download_path": self.download_path.get(),
            "selected_mode": self.selected_mode.get(),
            "is_playlist": self.is_playlist.get(),
            "cookie_source": self.cookie_source.get(),
            "cookie_path": self.cookie_path.get(),
            "flatpak_browser": self.flatpak_browser.get(),
            "open_after_download": self.open_after_download.get(),
            "language": self.language.get(),
            "appearance_mode": self.appearance_mode.get(),
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def clear_history(self):
        lang = self.language.get()
        if messagebox.askyesno(
            fix_text(TRANSLATIONS[lang]["confirm_title"], lang),
            fix_text(TRANSLATIONS[lang]["clear_history_confirm"], lang)
        ):
            try:
                with open(self.history_file, "w") as f:
                    json.dump([], f)

                to_remove = []
                for item_id, item in self.active_downloads.items():
                    if getattr(item, 'is_history', False):
                        to_remove.append(item_id)

                for item_id in to_remove:
                    item = self.active_downloads[item_id]
                    item.destroy()
                    del self.active_downloads[item_id]

                self._grid_downloads()

                messagebox.showinfo(
                    fix_text(TRANSLATIONS[lang]["success_title"], lang),
                    fix_text(TRANSLATIONS[lang]["clear_history_success"], lang)
                )
            except Exception as e:
                messagebox.showerror(
                    fix_text(TRANSLATIONS[lang]["error_title"], lang),
                    f"{fix_text(TRANSLATIONS[lang]['clear_history_error'], lang)}: {e}"
                )

    def _load_history(self):
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r") as f:
                history = json.load(f)
        except Exception:
            return
        lang = self.language.get()
        for entry in reversed(history):
            title = entry.get("title", "Unknown")
            ext = entry.get("ext", "unknown")
            file_path = entry.get("file_path", "")
            url = entry.get("url", "")
            item = DownloadItem(self.download_area, title, ext, file_path=file_path, url=url, lang=lang, is_history=True)
            item.set_file_path(file_path)
            item.progress_bar.set(1.0)
            item.set_state("completed")
            item.on_completed = self._save_history_item
            item_id = title + str(len(self.active_downloads))
            self.active_downloads[item_id] = item
        self._grid_downloads()

    def _save_history_item(self, title, file_path, ext, url):
        try:
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    history = json.load(f)
            entry = {
                "title": title,
                "ext": ext,
                "file_path": file_path,
                "url": url,
                "timestamp": str(datetime.now())
            }
            history.insert(0, entry)
            if len(history) > 100:
                history = history[:100]
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def on_closing(self):
        self.save_settings()
        self._save_session()
        self.iconify()

    def _exit_app(self):
        self._save_session()
        self._dm.cancel_all()
        self._api.stop()
        self._release_lock()
        self.destroy()
        sys.exit(0)

    def _save_session(self):
        try:
            pending = {k: v for k, v in self.active_downloads.items()
                       if getattr(v, '_state', '') in ('queued', 'downloading', 'paused')}
            if not pending:
                self._clear_session()
                return
            active_items = self._save_item_data(pending)
            with open(self._session_file, "w") as f:
                json.dump(active_items, f, indent=2)
        except Exception as e:
            print(f"Error saving session: {e}")

    def _save_item_data(self, items_dict):
        data = {}
        for item_id, item in items_dict.items():
            data[item_id] = {
                'title': getattr(item, '_title', 'Downloading...'),
                'ext': getattr(item, '_ext', 'unknown'),
                'url': getattr(item, '_url', ''),
                'file_path': getattr(item, '_file_path', ''),
                'state': getattr(item, '_state', 'queued'),
                'progress': getattr(item, '_last_percent', 0),
                'is_history': getattr(item, 'is_history', False),
                'snapshots': getattr(item, '_snapshots', None),
            }
        with self._queue_lock:
            queue_ids = [i for i in self._download_queue if i in items_dict]
            active_id = self._active_item_id if self._active_item_id in items_dict else None
        data['_queue_meta'] = {
            'queue_ids': queue_ids,
            'active_id': active_id,
        }
        return data

    def _restore_session(self):
        if not os.path.exists(self._session_file):
            return
        try:
            with open(self._session_file, "r") as f:
                saved = json.load(f)
            if not saved or '_queue_meta' not in saved:
                return
            active_items = {k: v for k, v in saved.items() if k != '_queue_meta'}
            if not active_items:
                self._clear_session()
                return

            self._rebuild_active_downloads(saved)
            self._clear_session()
        except Exception as e:
            print(f"Error restoring session: {e}")
            self._clear_session()

    def _clear_session(self):
        try:
            if os.path.exists(self._session_file):
                os.remove(self._session_file)
        except Exception as e:
            print(f"Error clearing session: {e}")

    def _session_timer(self):
        if self.active_downloads:
            self._save_session()
        self.after(15000, self._session_timer)

    def _dir(self, is_rtl):
        return "e" if is_rtl else "w"

    def _justify(self, is_rtl):
        return "right" if is_rtl else "left"

    def _side_start(self, is_rtl):
        return "right" if is_rtl else "left"

    def _side_end(self, is_rtl):
        return "left" if is_rtl else "right"

    def setup_ui(self):
        lang = self.language.get()
        is_rtl = lang == "Arabic"

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=380)
        self.grid_rowconfigure(0, weight=1)

        self.download_area = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.download_area.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.download_area.grid_columnconfigure(0, weight=1)

        self.settings_panel = ctk.CTkFrame(self, fg_color=COLORS["surface"], corner_radius=0, border_width=0)
        self.settings_panel.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.settings_panel.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self.settings_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(28, 20))

        header_icon = ctk.CTkLabel(
            header_frame,
            text=fix_text(TRANSLATIONS[lang]["settings"], lang),
            font=get_font("heading", lang),
            text_color=COLORS["text_heading"]
        )
        header_icon.pack(anchor="center")

        sub_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        sub_frame.pack(anchor="center", pady=(2, 0))

        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extension", "icons", "icon48.png")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "share", "icons", "hicolor", "48x48", "apps", "com.boussari.downloader.png")
            if os.path.exists(icon_path):
                pil_img = Image.open(icon_path)
                ctk_img = ctk.CTkImage(pil_img, size=(18, 18))
                logo_label = ctk.CTkLabel(sub_frame, image=ctk_img, text="")
                logo_label.pack(side="left", padx=(0, 6))
        except Exception:
            pass

        header_sub = ctk.CTkLabel(
            sub_frame,
            text=fix_text("Boussari Download v1.0", lang),
            font=get_font("subheading", lang),
            text_color=COLORS["primary_light"]
        )
        header_sub.pack(side="left")

        url_card = make_card(self.settings_panel)
        url_card.pack(fill="x", padx=20, pady=6)

        make_icon_label(url_card, ICONS["link"], TRANSLATIONS[lang]["url_label"], lang).pack(
            padx=16, pady=(14, 6), anchor=self._dir(is_rtl))

        url_entry_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        url_entry_frame.pack(fill="x", padx=16, pady=(0, 4))

        self.url_entry = ctk.CTkEntry(
            url_entry_frame,
            placeholder_text="https://youtube.com/watch?v=...",
            height=40,
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["input_border"],
            corner_radius=10,
            font=get_font("body", lang),
            justify=self._justify(is_rtl)
        )
        self.url_entry.pack(side=self._side_start(is_rtl), fill="x", expand=True,
                            padx=(0, 8) if not is_rtl else (8, 0))

        self.paste_btn = ctk.CTkButton(
            url_entry_frame,
            text=f"{ICONS['paste']}",
            width=40, height=40,
            corner_radius=10,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            font=get_font("body", lang),
            command=self.paste_url
        )
        self.paste_btn.pack(side=self._side_end(is_rtl))

        self.playlist_check = ctk.CTkCheckBox(
            url_card,
            text=f"  {fix_text(TRANSLATIONS[lang]['playlist_check'], lang)}",
            variable=self.is_playlist,
            command=self.toggle_playlist_label,
            font=get_font("body", lang),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=6,
            border_width=2,
            border_color=COLORS["border"]
        )
        self.playlist_check.pack(anchor=self._dir(is_rtl), padx=16, pady=(8, 6))

        self.playlist_status_label = ctk.CTkLabel(
            url_card,
            textvariable=self.playlist_status,
            font=get_font("body_bold", lang),
            text_color=COLORS["primary_light"]
        )
        self.playlist_status_label.pack(anchor=self._dir(is_rtl), padx=16, pady=(0, 12))
        self.toggle_playlist_label()

        storage_card = make_card(self.settings_panel)
        storage_card.pack(fill="x", padx=20, pady=6)

        make_icon_label(storage_card, ICONS["folder"], TRANSLATIONS[lang]["storage_label"], lang).pack(
            padx=16, pady=(14, 6), anchor=self._dir(is_rtl))

        path_frame = ctk.CTkFrame(storage_card, fg_color="transparent")
        path_frame.pack(fill="x", padx=16, pady=(0, 14))

        path_input_frame = ctk.CTkFrame(
            path_frame,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["input_border"],
            border_width=1,
            corner_radius=10,
        )
        path_input_frame.pack(side=self._side_start(is_rtl), fill="x", expand=True,
                              padx=(0, 8) if not is_rtl else (8, 0))

        self.path_entry = ctk.CTkEntry(
            path_input_frame,
            textvariable=self.download_path,
            height=38,
            fg_color="transparent",
            border_width=0,
            font=get_font("body", lang),
            justify=self._justify(is_rtl)
        )
        self.path_entry.pack(side=self._side_start(is_rtl), fill="x", expand=True, padx=(12, 0))

        self.path_btn = ctk.CTkButton(
            path_input_frame,
            text=f"{ICONS['folder']}",
            width=40, height=38,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_secondary"],
            font=get_font("body", lang),
            command=self.browse_folder
        )
        self.path_btn.pack(side=self._side_end(is_rtl), padx=(0, 4))

        self.download_btn = ctk.CTkButton(
            path_frame,
            text=f"{ICONS['download']} {fix_text(TRANSLATIONS[lang]['start_btn'], lang)}",
            height=40,
            corner_radius=10,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#ffffff",
            font=get_font("body_bold", lang),
            command=self.start_download_thread
        )
        self.download_btn.pack(side=self._side_end(is_rtl), padx=(8, 0) if not is_rtl else (0, 8))

        options_card = make_card(self.settings_panel)
        options_card.pack(fill="x", padx=20, pady=6)
        options_card.grid_columnconfigure(1, weight=1)

        self._build_options_grid(options_card, lang, is_rtl)

        bottom_card = make_card(self.settings_panel, fg_color="transparent", border_width=0)
        bottom_card.pack(fill="x", padx=20, pady=(6, 20))

        self.guide_btn = ctk.CTkButton(
            bottom_card,
            text=f"{ICONS['guide']}  {fix_text(TRANSLATIONS[lang]['guide'], lang)}",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_secondary"],
            font=get_font("body", lang),
            border_width=1,
            border_color=COLORS["border"],
            command=self.show_guide
        )
        self.guide_btn.pack(side="left" if not is_rtl else "right", padx=10, pady=5, expand=True)

        self.about_btn = ctk.CTkButton(
            bottom_card,
            text=f"{ICONS['info']}  {fix_text(TRANSLATIONS[lang]['about'], lang)}",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_secondary"],
            font=get_font("body", lang),
            border_width=1,
            border_color=COLORS["border"],
            command=self.show_about
        )
        self.about_btn.pack(side="left" if not is_rtl else "right", padx=10, pady=5, expand=True)

        self.exit_btn = ctk.CTkButton(
            bottom_card,
            text=f"{ICONS['cancel']}  {fix_text(TRANSLATIONS[lang]['exit'], lang)}",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=COLORS["error_bg"],
            text_color=COLORS["error"],
            font=get_font("body", lang),
            border_width=1,
            border_color=COLORS["error_bg"],
            command=self._exit_app
        )
        self.exit_btn.pack(side="right" if not is_rtl else "left", padx=10, pady=5, expand=True)

        self.clear_history_btn = ctk.CTkButton(
            bottom_card,
            text=f"{ICONS['cancel']}  {fix_text(TRANSLATIONS[lang]['clear_history'], lang)}",
            height=38,
            corner_radius=10,
            fg_color="transparent",
            hover_color=COLORS["error_bg"],
            text_color=COLORS["error"],
            font=get_font("body", lang),
            border_width=1,
            border_color=COLORS["error_bg"],
            command=self.clear_history
        )
        self.clear_history_btn.pack(side="right" if not is_rtl else "left", padx=10, pady=5, expand=True)

    def _build_options_grid(self, parent, lang, is_rtl=False):
        padding = {"padx": 16, "pady": (10, 4)}
        sticky_label = "e" if is_rtl else "w"

        make_icon_label(parent, ICONS["video"], TRANSLATIONS[lang]["quality_label"], lang).grid(
            row=0, column=0, **padding, sticky=sticky_label)
        mode_keys = list(QUALITY_TEMPLATES.keys())
        SEP = "\u2500" * 20
        mode_display = []
        for m in mode_keys:
            if m in ("best_audio_mp3", "video_no_audio"):
                mode_display.append(SEP)
            mode_display.append(QUALITY_TEMPLATES[m]["description"])
        self.mode_menu = ctk.CTkOptionMenu(
            parent,
            values=mode_display,
            command=self.update_mode_value,
            fg_color=COLORS["input_bg"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text"],
            text_color=COLORS["text"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        current_mode = self.selected_mode.get()
        self.mode_menu.set(QUALITY_TEMPLATES[current_mode]["description"])
        self.mode_menu.grid(row=0, column=1, **padding, sticky="ew")

        from config import SUPPORTED_BROWSERS
        make_icon_label(parent, ICONS["globe"], TRANSLATIONS[lang]["cookies_label"], lang).grid(
            row=1, column=0, **padding, sticky=sticky_label)
        self.cookie_menu = ctk.CTkOptionMenu(
            parent,
            values=SUPPORTED_BROWSERS,
            variable=self.cookie_source,
            command=self.toggle_cookie_options,
            fg_color=COLORS["input_bg"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text"],
            text_color=COLORS["text"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        self.cookie_menu.grid(row=1, column=1, **padding, sticky="ew")

        make_icon_label(parent, ICONS["globe"], TRANSLATIONS[lang]["lang_label"], lang).grid(
            row=2, column=0, **padding, sticky=sticky_label)
        self.lang_menu = ctk.CTkOptionMenu(
            parent,
            values=["Arabic", "English"],
            variable=self.language,
            command=self.update_language_ui,
            fg_color=COLORS["input_bg"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text"],
            text_color=COLORS["text"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        self.lang_menu.grid(row=2, column=1, **padding, sticky="ew")

        make_icon_label(parent, ICONS["star"], TRANSLATIONS[lang]["theme_label"], lang).grid(
            row=3, column=0, **padding, sticky=sticky_label)
        self.theme_menu = ctk.CTkOptionMenu(
            parent,
            values=["dark", "light"],
            variable=self.appearance_mode,
            command=self.toggle_appearance_mode,
            fg_color=COLORS["input_bg"],
            button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_hover_color=COLORS["card_hover"],
            dropdown_text_color=COLORS["text"],
            text_color=COLORS["text"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        self.theme_menu.grid(row=3, column=1, **padding, sticky="ew")

        self.cookie_extra_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.cookie_extra_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 10))
        self.cookie_extra_frame.grid_columnconfigure(0, weight=1)

        self.custom_file_frame = ctk.CTkFrame(self.cookie_extra_frame, fg_color="transparent")
        self.custom_file_frame.grid_columnconfigure(0, weight=1)

        self.custom_file_entry = ctk.CTkEntry(
            self.custom_file_frame,
            textvariable=self.cookie_path,
            placeholder_text="path/to/cookies.txt...",
            height=36,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["input_border"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        self.custom_file_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.custom_file_btn = ctk.CTkButton(
            self.custom_file_frame,
            text=f"{ICONS['folder']}",
            width=36, height=36,
            corner_radius=10,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=get_font("small", lang),
            command=self.browse_cookie_file
        )
        self.custom_file_btn.grid(row=0, column=1)

        self.flatpak_frame = ctk.CTkFrame(self.cookie_extra_frame, fg_color="transparent")
        self.flatpak_frame.grid_columnconfigure(0, weight=1)

        self.flatpak_browser_entry = ctk.CTkEntry(
            self.flatpak_frame,
            textvariable=self.flatpak_browser,
            placeholder_text="browser",
            width=80, height=36,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["input_border"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        self.flatpak_browser_entry.grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.flatpak_path_entry = ctk.CTkEntry(
            self.flatpak_frame,
            textvariable=self.cookie_path,
            placeholder_text="Flatpak profile path...",
            height=36,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["input_border"],
            corner_radius=10,
            font=get_font("body", lang)
        )
        self.flatpak_path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))

        self.flatpak_btn = ctk.CTkButton(
            self.flatpak_frame,
            text=f"{ICONS['folder']}",
            width=36, height=36,
            corner_radius=10,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=get_font("small", lang),
            command=self.browse_flatpak_profile
        )
        self.flatpak_btn.grid(row=0, column=2)

        self.cookie_extra_frame.grid_remove()

    def toggle_playlist_label(self):
        lang = self.language.get()
        is_rtl = lang == "Arabic"
        if self.is_playlist.get():
            self.playlist_status_label.pack(anchor="e" if is_rtl else "w", padx=16, pady=(0, 12))
        else:
            self.playlist_status_label.pack_forget()

    def update_mode_value(self, choice):
        if len(choice) > 10 and all(c in "\u2500" for c in choice.strip("\u2500")):
            return
        for key, val in QUALITY_TEMPLATES.items():
            if val["description"] == choice:
                self.selected_mode.set(key)
                self.save_settings()
                break

    def _apply_theme(self):
        mode = self.appearance_mode.get()
        global COLORS
        COLORS = DARK_COLORS if mode == "dark" else LIGHT_COLORS
        ctk.set_appearance_mode(mode)

    def toggle_appearance_mode(self, choice):
        self._apply_theme()
        self.save_settings()
        saved = self._save_active_item_data()
        self.active_downloads.clear()
        for w in (getattr(self, 'download_area', None), getattr(self, 'settings_panel', None)):
            if w and w.winfo_exists():
                w.destroy()
        self.setup_ui()
        self._rebuild_active_downloads(saved)

    def update_language_ui(self, choice):
        self.save_settings()
        self.playlist_status.set(fix_text(TRANSLATIONS[choice]["no_playlist"], choice))
        saved = self._save_active_item_data()
        self.active_downloads.clear()
        for w in (getattr(self, 'download_area', None), getattr(self, 'settings_panel', None)):
            if w and w.winfo_exists():
                w.destroy()
        self.setup_ui()
        self._rebuild_active_downloads(saved)

    def show_guide(self):
        lang = self.language.get()
        guide_win = ctk.CTkToplevel(self)
        guide_win.title(fix_text(TRANSLATIONS[lang]["guide_title"], lang))
        guide_win.geometry("560x500")
        guide_win.configure(fg_color=COLORS["bg"])
        guide_win.after(10, guide_win.lift)
        guide_win.resizable(False, False)

        main_frame = ctk.CTkFrame(guide_win, fg_color=COLORS["card"], corner_radius=18, border_width=1, border_color=COLORS["border"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main_frame,
            text=fix_text(TRANSLATIONS[lang]["guide_title"], lang),
            font=get_font("heading", lang),
            text_color=COLORS["text_heading"]
        ).pack(pady=(24, 12))

        text_widget = ctk.CTkTextbox(
            main_frame,
            wrap="word",
            font=get_font("body", "English"),
            text_color=COLORS["text"],
            fg_color="transparent",
            border_width=0,
            height=320
        )
        text_widget.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        text_widget.insert("1.0", GUIDE_TEXT)
        text_widget.configure(state="disabled")

        ctk.CTkButton(
            main_frame,
            text=f"{ICONS['check']}  {fix_text(TRANSLATIONS[lang]['close'], lang)}",
            height=38, corner_radius=10,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#ffffff",
            font=get_font("body_bold", lang),
            command=guide_win.destroy
        ).pack(pady=(0, 22))

    def show_about(self):
        lang = self.language.get()
        about_win = ctk.CTkToplevel(self)
        about_win.title(fix_text(TRANSLATIONS[lang]["about"], lang))
        about_win.geometry("480x420")
        about_win.configure(fg_color=COLORS["bg"])
        about_win.after(10, about_win.lift)
        about_win.resizable(False, False)

        main_frame = ctk.CTkFrame(about_win, fg_color=COLORS["card"], corner_radius=18, border_width=1, border_color=COLORS["border"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extension", "icons", "icon128.png")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "share", "icons", "hicolor", "128x128", "apps", "com.boussari.downloader.png")
            if os.path.exists(icon_path):
                pil_img = Image.open(icon_path)
                ctk_img = ctk.CTkImage(pil_img, size=(64, 64))
                ctk.CTkLabel(main_frame, image=ctk_img, text="").pack(pady=(28, 10))
        except Exception:
            pass

        ctk.CTkLabel(
            main_frame,
            text="Boussari Download",
            font=get_font("heading", lang),
            text_color=COLORS["text_heading"]
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            main_frame,
            text=TRANSLATIONS[lang]["version"],
            font=get_font("body", lang),
            text_color=COLORS["primary_light"]
        ).pack(pady=(0, 18))

        ctk.CTkLabel(
            main_frame,
            text=fix_text(TRANSLATIONS[lang]["dev_info"], "English"),
            font=get_font("body", "English"),
            text_color=COLORS["text_secondary"],
            wraplength=420,
            justify="left"
        ).pack(padx=28, pady=(0, 18))

        ctk.CTkButton(
            main_frame,
            text=f"{ICONS['check']}  {fix_text(TRANSLATIONS[lang]['close'], lang)}",
            height=38, corner_radius=10,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color="#ffffff",
            font=get_font("body_bold", lang),
            command=about_win.destroy
        ).pack(pady=(0, 22))

    def toggle_cookie_options(self, choice):
        for child in self.cookie_extra_frame.winfo_children():
            child.grid_remove()
        self.cookie_extra_frame.grid_remove()

        if choice == "Custom File":
            self.custom_file_frame.grid(row=0, column=0, sticky="ew")
            self.cookie_extra_frame.grid()
        elif choice == "Flatpak":
            if self.flatpak_browser.get() == "firefox":
                base_path = os.path.expanduser("~/.var/app/org.mozilla.firefox/.mozilla/firefox")
                profiles = glob.glob(os.path.join(base_path, "*.default-release"))
                if profiles:
                    self.cookie_path.set(profiles[0])
                else:
                    self.cookie_path.set(base_path)
            self.flatpak_frame.grid(row=0, column=0, sticky="ew")
            self.cookie_extra_frame.grid()

    def browse_cookie_file(self):
        file = filedialog.askopenfilename(title="Select cookies.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file:
            self.cookie_path.set(file)

    def browse_flatpak_profile(self):
        folder = filedialog.askdirectory(title="Select Flatpak Profile Folder", initialdir=os.path.expanduser("~/.var/app"))
        if folder:
            self.cookie_path.set(folder)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)
            self.save_settings()

    def _progress_line(self, item_id, line):
        line = line.strip()
        if not line:
            return

        item = self.active_downloads.get(item_id)
        if not item:
            return

        playlist_match = re.search(r"\[download\] Downloading (.+?) (\d+) of (.+)", line)
        if playlist_match:
            index = int(playlist_match.group(2))
            total_str = playlist_match.group(3).strip()
            lang = self.language.get()
            kind = playlist_match.group(1).lower()
            key = "audio_of" if kind.startswith("audio") else "video_of"
            try:
                total = int(total_str)
                text = TRANSLATIONS[lang][key].format(index=index, total=total)
            except ValueError:
                text = TRANSLATIONS[lang][key].format(index=index, total=total_str)
            self.after(0, lambda t=text: self.playlist_status.set(fix_text(t, self.language.get())))
            return

        total_match = re.search(r"Downloading (\d+) (audio )?items", line)
        if total_match:
            total = int(total_match.group(1))
            lang = self.language.get()
            is_audio = bool(total_match.group(2))
            key = "audio_of" if is_audio else "video_of"
            text = TRANSLATIONS[lang][key].format(index=1, total=total)
            self.after(0, lambda t=text: self.playlist_status.set(fix_text(t, self.language.get())))
            return

        if "progress_mode: indeterminate" in line:
            self.after(0, lambda iid=item_id: self._set_indeterminate(iid))
            return

        if "Destination:" in line:
            try:
                filename = line.split("Destination:")[1].strip()
                base = os.path.basename(filename)
                name, ext = os.path.splitext(base)
                clean_name = re.sub(r'\.f\d+', '', name)
                self.after(0, lambda cn=clean_name: item.title_label.configure(
                    text=f"{ICONS['pencil']}  {fix_text(cn, item._lang)}"))
                new_ext = ext[1:] if ext else "unknown"
                type_icon = ICONS["music"] if new_ext in ("mp3", "m4a", "aac", "flac", "wav", "opus") else ICONS["video"]
                self.after(0, lambda icon=type_icon, e=new_ext: item.ext_label.configure(
                    text=f"{icon}  .{e}"))
                self.after(0, lambda e=new_ext: setattr(item, '_ext', e))
                self.after(0, lambda fp=filename: item.set_file_path(fp))
            except Exception:
                pass
            return

        if "has already been downloaded" in line:
            try:
                fp = line.split("]")[-1].strip().rsplit(" has", 1)[0]
                self.after(0, lambda fp=fp: item.set_file_path(fp))
            except Exception:
                pass
            self.after(0, lambda: item.progress_bar.set(1.0))
            self.after(0, lambda: setattr(item, '_already_existed', True))
            return

        pct_match = re.search(r"(\d+\.?\d*)%", line)
        if pct_match:
            try:
                percent = float(pct_match.group(1))
                size_match = re.search(r"%\s+of\s+(.+?)\s+at\s+", line)
                size = size_match.group(1).strip() if size_match else ""
                speed_match = re.search(r"at\s+([\d.]+\s*\S+/s)", line)
                speed = speed_match.group(1).strip() if speed_match else ""
                eta_match = re.search(r"ETA\s+([\d:]+)", line)
                eta = eta_match.group(1) if eta_match else None
                ext = item._ext

                now = time.time()
                if now - getattr(item, '_last_ui_update', 0) < 0.1:
                    return
                item._last_ui_update = now
                self.after(0, lambda p=percent, s=speed, sz=size, et=eta, ex=ext:
                           item.update_progress(p, s, ex, sz, et))
            except Exception as ex:
                print(f"Progress parse error: {ex}")

    def _set_indeterminate(self, item_id):
        item = self.active_downloads.get(item_id)
        if item and item.winfo_exists():
            item.progress_bar.configure(mode="indeterminate")
            item.progress_bar.start()

    def paste_url(self):
        try:
            url = self.clipboard_get()
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, url)
        except Exception as e:
            print(f"[Paste] Failed: {e}")

    def _save_active_item_data(self):
        data = {}
        for item_id, item in list(self.active_downloads.items()):
            data[item_id] = {
                'title': getattr(item, '_title', 'Downloading...'),
                'ext': getattr(item, '_ext', 'unknown'),
                'url': getattr(item, '_url', ''),
                'file_path': getattr(item, '_file_path', ''),
                'state': getattr(item, '_state', 'queued'),
                'progress': getattr(item, '_last_percent', 0),
                'is_history': getattr(item, 'is_history', False),
                'snapshots': getattr(item, '_snapshots', None),
            }
        data['_queue_meta'] = {
            'queue_ids': list(self._download_queue),
            'active_id': self._active_item_id,
        }
        return data

    def _rebuild_active_downloads(self, saved_data):
        queue_ids = []
        active_id = None
        if '_queue_meta' in saved_data:
            queue_ids = saved_data['_queue_meta'].get('queue_ids', [])
            active_id = saved_data['_queue_meta'].get('active_id')
            del saved_data['_queue_meta']

        for item_id, data in saved_data.items():
            item = DownloadItem(
                self.download_area,
                data['title'], data['ext'],
                file_path=data['file_path'],
                url=data['url'],
                lang=self.language.get(),
                is_history=data['is_history'],
            )
            if data.get('snapshots'):
                item._snapshots = data['snapshots']
            if data['is_history']:
                item.on_completed = self._save_history_item
            else:
                item.on_pause = self._pause_download
                item.on_resume = self._resume_download
                item.on_retry = self._retry_download
                item.on_cancel = self._cancel_download
                item.on_completed = self._save_history_item
            item.set_state(data['state'])
            if data.get('progress', 0) > 0:
                pct = data['progress']
                item._last_percent = pct
                item.progress_bar.set(min(pct / 100.0, 1.0))
            if data['file_path']:
                item.set_file_path(data['file_path'])
            self.active_downloads[item_id] = item
        self._grid_downloads()

        with self._queue_lock:
            self._download_queue = [i for i in queue_ids if i in self.active_downloads]
            if active_id and active_id in self.active_downloads:
                self._active_item_id = None
        if active_id:
            self.after(200, self._process_queue)

    def _grid_downloads(self):
        for existing_item in list(self.active_downloads.values()):
            try:
                if existing_item.winfo_exists():
                    existing_item.grid_forget()
            except Exception:
                pass
        row = 1
        for item in reversed(list(self.active_downloads.values())):
            try:
                if item.winfo_exists():
                    item.grid(row=row, column=0, padx=12, pady=6, sticky="ew")
                    row += 1
            except Exception:
                pass

    def start_download_thread(self):
        try:
            lang = self.language.get()
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showwarning(
                    fix_text(TRANSLATIONS[lang]["error_title"], lang),
                    fix_text(TRANSLATIONS[lang]["enter_url_first"], lang)
                )
                return

            placeholder_title = url.split("/")[-1][:40] if "/" in url else url[:40]
            item = DownloadItem(self.download_area, placeholder_title, "unknown", lang=lang, url=url)
            item.on_pause = self._pause_download
            item.on_resume = self._resume_download
            item.on_retry = self._retry_download
            item.on_cancel = self._cancel_download
            item.on_completed = self._save_history_item
            item_id = placeholder_title + str(len(self.active_downloads))
            self.active_downloads[item_id] = item
            item.set_state("queued")
            self._grid_downloads()

            mode = self._extension_format if self._extension_format else self.selected_mode.get()
            self._extension_format = None
            snapshots = {
                "mode": mode,
                "is_playlist": self.is_playlist.get(),
                "cookie_source": self.cookie_source.get(),
                "cookie_path": self.cookie_path.get(),
                "flatpak_browser": self.flatpak_browser.get(),
                "open_after": self.open_after_download.get(),
                "download_path": self.download_path.get(),
            }
            snapshots["url"] = url
            item._snapshots = snapshots
            self._dm.register_item(item_id)

            with self._queue_lock:
                self._download_queue.append(item_id)
            self._process_queue()
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to start download:\n{e}")

    def _process_queue(self):
        with self._queue_lock:
            if self._active_item_id is not None:
                return
            if not self._download_queue:
                return
            item_id = self._download_queue.pop(0)
            self._active_item_id = item_id

        item = self.active_downloads.get(item_id)
        if not item:
            with self._queue_lock:
                self._active_item_id = None
            return

        if hasattr(item, '_snapshots') and item._snapshots:
            snapshots = item._snapshots
        else:
            snapshots = {
                "url": item._url,
                "mode": self.selected_mode.get(),
                "is_playlist": self.is_playlist.get(),
                "cookie_source": self.cookie_source.get(),
                "cookie_path": self.cookie_path.get(),
                "flatpak_browser": self.flatpak_browser.get(),
                "open_after": self.open_after_download.get(),
                "download_path": self.download_path.get(),
            }
        self._dm.register_item(item_id)

        def on_downloading():
            self.after(0, lambda: self.active_downloads[item_id].set_state("downloading"))

        def on_completed(snap):
            self.after(0, lambda s=snap: self.active_downloads[item_id].set_state("completed"))
            if snap["open_after"]:
                self.after(0, lambda: subprocess.run(["xdg-open", snap["download_path"]]))
            self.after(0, lambda: subprocess.run(["notify-send", "LinuxDownloader", "Download complete!"], stderr=subprocess.DEVNULL))
            with self._queue_lock:
                self._active_item_id = None
            self._save_session()
            self._process_queue()

        def on_error():
            self.after(0, lambda: self.active_downloads[item_id].set_state("error"))
            with self._queue_lock:
                self._active_item_id = None
            self._save_session()
            self._process_queue()

        self._dm.launch(
            item_id, snapshots,
            on_downloading=on_downloading,
            on_progress=lambda line: self._progress_line(item_id, line),
            on_completed=on_completed,
            on_error=on_error
        )

    def _pause_download(self, title):
        for item_id, item in self.active_downloads.items():
            if item._title == title:
                self._dm.pause(item_id)
                item.set_state("paused")
                break

    def _resume_download(self, title):
        for item_id, item in self.active_downloads.items():
            if item._title == title:
                item.set_state("queued")
                item._snapshots = {
                    "url": item._url,
                    "mode": self.selected_mode.get(),
                    "is_playlist": self.is_playlist.get(),
                    "cookie_source": self.cookie_source.get(),
                    "cookie_path": self.cookie_path.get(),
                    "flatpak_browser": self.flatpak_browser.get(),
                    "open_after": self.open_after_download.get(),
                    "download_path": self.download_path.get(),
                }
                with self._queue_lock:
                    if item_id not in self._download_queue:
                        self._download_queue.append(item_id)
                self._process_queue()
                break

    def _retry_download(self, title):
        self._resume_download(title)

    def _cancel_download(self, title):
        to_remove = []
        for item_id, item in self.active_downloads.items():
            if item._title == title:
                with self._queue_lock:
                    if item_id in self._download_queue:
                        self._download_queue.remove(item_id)
                    if self._active_item_id == item_id:
                        self._active_item_id = None
                self._dm.cancel(item_id)
                item.destroy()
                to_remove.append(item_id)
        for item_id in to_remove:
            del self.active_downloads[item_id]
        self._grid_downloads()
        self._save_session()
        with self._queue_lock:
            if self._active_item_id is None and self._download_queue:
                self.after(0, self._process_queue)


if __name__ == "__main__":
    app = App()
    app.mainloop()
