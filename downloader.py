import subprocess
import os
import re
import time
import urllib.request
import urllib.error
import urllib.parse
import json
from http.cookiejar import CookieJar
from config import DEFAULT_FLAGS, PLAYLIST_FLAGS, QUALITY_TEMPLATES, OUTPUT_TEMPLATE, SUBFOLDERS, get_subfolder
from logger import logger

AUDIO_EXTS = (".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac", ".wma")

DIRECT_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".msi", ".dmg", ".deb", ".rpm", ".apk",
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".3gp",
    ".mp3", ".flac", ".wav", ".aac", ".m4a", ".ogg", ".opus", ".wma",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
    ".iso", ".img",
    ".py", ".js", ".ts", ".html", ".css",
    ".csv", ".json", ".xml",
}


def is_direct_url(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    for ext in DIRECT_EXTENSIONS:
        if path.endswith(ext):
            return True
    if '/stream/' in path:
        return True
    return False


def clean_title(text):
    """Remove emojis, symbols, and special characters from titles."""
    if not text:
        return text
    text = text.strip()
    text = re.sub(
        r'[\U0001F000-\U0001FFFF\U0000FE00-\U0000FE0F\u2700-\u27BF'
        r'\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2300-\u23FF\u2500-\u257F'
        r'\u25A0-\u25FF\u2100-\u214F\u2190-\u21FF\u200D\u200C\uFE00-\uFE0F'
        r'\u00A9\u00AE\u2122\u2665\u2666\u266A\u266B\u266C\u2660\u2663'
        r'\u2667\u2668\u2669\u266D\u266E\u266F\u2702\u2708\u2709\u270A'
        r'\u270B\u270C\u270D\u270E\u270F\u2712\u2714\u2716\u2728\u2733'
        r'\u2734\u2744\u2747\u274C\u274E\u2753\u2754\u2755\u2757\u2763'
        r'\u2764\u2795\u2796\u2797\u27A1\u27B0\u27BF]+', '', text
    )
    text = re.sub(r'[^\w\s\-\'\.\,\!\?\(\)\[\]\u0600-\u06FF\u0400-\u04FF\u00C0-\u024F\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class YtDownloader:
    def __init__(self, download_path):
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)

    def build_command(self, url, mode, is_playlist=True, cookie_source="default", cookie_path=None, flatpak_browser=None):
        cmd = ["yt-dlp"]
        
        # 1. Cookies
        if cookie_source != "default":
            if cookie_source == "Custom File":
                if cookie_path:
                    cmd.extend(["--cookies", cookie_path])
            elif cookie_source == "Flatpak":
                if flatpak_browser and cookie_path:
                    cmd.extend(["--cookies-from-browser", f"{flatpak_browser}:{cookie_path}"])
            else:
                cmd.extend(["--cookies-from-browser", cookie_source])
        
        # 2. Default flags (retries, js-runtime, etc.)
        cmd.extend(DEFAULT_FLAGS)
        
        # 3. Quality & Format
        template = QUALITY_TEMPLATES.get(mode)
        if template:
            cmd.extend(["-f", template["format"]])
            if template.get("merge_format"):
                cmd.extend(["--merge-output-format", template["merge_format"]])
            if template.get("extract_audio"):
                cmd.extend(["-x", "--audio-format", template["audio_format"], "--audio-quality", template["audio_quality"]])
        else:
            # Raw yt-dlp format ID from browser extension (e.g. "22", "137", "bestvideo")
            cmd.extend(["-f", mode])
            
        # 4. Playlist/Single
        if not is_playlist:
            cmd.append("--no-playlist")
        else:
            cmd.append("--yes-playlist")
            cmd.extend(PLAYLIST_FLAGS)
            
        # 5. Additional flags
        cmd.extend(["--no-warnings", "--newline"])
        
        # 6. Output Template
        subfolder = get_subfolder("", mode)
        if is_playlist:
            template = "%(playlist_title)s/%(title)s.%(ext)s"
        else:
            template = "%(title)s.%(ext)s"
        full_output_template = os.path.join(self.download_path, subfolder, template)
        cmd.extend(["-o", full_output_template])
        
        # 7. URL
        cmd.append(url)
        
        return cmd

    def list_formats(self, url):
        try:
            result = subprocess.run(
                ["yt-dlp", "-J", "--no-warnings", url],
                capture_output=True, text=True, timeout=30
            )
            data = json.loads(result.stdout)
            raw = data.get("formats") or data.get("requested_formats") or []
            formats = []
            for f in raw:
                formats.append({
                    "id": f.get("format_id", ""),
                    "ext": f.get("ext", ""),
                    "resolution": f.get("resolution", "") or f.get("format_note", "") or ""
                })
            return formats
        except Exception as e:
            return []

    def download(self, url, mode, is_playlist=True, cookie_source="default", cookie_path=None, flatpak_browser=None, progress_callback=None, cancel_check=None):
        # Direct URLs go to DirectDownloader
        if is_direct_url(url):
            logger.info(f"Direct URL detected, using DirectDownloader for {url}")
            direct_dl = DirectDownloader(self.download_path)
            return direct_dl.download(url, progress_callback=progress_callback, cancel_check=cancel_check)

        last_dest_path = None
        for attempt in range(2):
            try:
                actual_cookie = cookie_source if attempt == 0 else "default"
                cmd = self.build_command(url, mode, is_playlist, actual_cookie, cookie_path, flatpak_browser)
                logger.info(f"Executing CLI command: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    encoding='utf-8'
                )
                
                output_lines = []
                for line in process.stdout:
                    output_lines.append(line)
                    if cancel_check and cancel_check():
                        process.terminate()
                        logger.info("Process terminated by user request.")
                        raise Exception("CANCELLED")
                    
                    if "Destination:" in line:
                        last_dest_path = line.split("Destination:", 1)[1].strip()
                    if progress_callback:
                        progress_callback(line)
                    logger.debug(f"yt-dlp: {line.strip()}")
                    
                process.wait()
                
                full_output = " ".join(output_lines)

                if attempt == 0 and "Requested format is not available" in full_output and cookie_source != "default":
                    logger.info("Format not available with cookies, retrying without cookies...")
                    continue

                if "Unsupported URL" in full_output:
                    logger.info("yt-dlp does not support this URL, scraping page for audio...")
                    direct_dl = DirectDownloader(self.download_path)
                    return direct_dl.scrape_and_download(url, progress_callback=progress_callback, cancel_check=cancel_check)

                if process.returncode != 0:
                    logger.error(f"Process failed with return code {process.returncode}")
                    return False

                downloaded = False
                if last_dest_path and os.path.exists(last_dest_path):
                    downloaded = os.path.getsize(last_dest_path) > 1024
                if not downloaded:
                    logger.error("No downloaded file found after yt-dlp completed")
                    return False

                logger.info(f"Download finished with return code {process.returncode}")
                return True
                    
            except Exception as e:
                if str(e) == "CANCELLED":
                    return False
                logger.error(f"An error occurred during execution: {str(e)}")
                return False
        return False


class DirectDownloader:
    def __init__(self, download_path):
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)

    def _get_filename(self, url, response):
        cd = response.headers.get("Content-Disposition")
        if cd:
            match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)', cd, re.IGNORECASE)
            if match:
                return urllib.parse.unquote(match.group(1))
        path = urllib.parse.urlparse(url).path
        return os.path.basename(urllib.parse.unquote(path)) or "download"

    def download(self, url, progress_callback=None, cancel_check=None, opener=None, filename_hint=None, subfolder_hint=None):
        try:
            ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

            total = 0
            try:
                head_req = urllib.request.Request(url, method='HEAD', headers={"User-Agent": ua})
                head_resp = opener.open(head_req, timeout=10) if opener else urllib.request.urlopen(head_req, timeout=10)
                total = int(head_resp.headers.get("Content-Length", 0))
                head_resp.close()
            except Exception:
                pass

            if total == 0:
                try:
                    range_req = urllib.request.Request(url, headers={"User-Agent": ua, "Range": "bytes=0-0"})
                    range_resp = opener.open(range_req, timeout=10) if opener else urllib.request.urlopen(range_req, timeout=10)
                    cr = range_resp.headers.get("Content-Range", "")
                    if "/" in cr:
                        total = int(cr.rsplit("/", 1)[1])
                    range_resp.close()
                except Exception:
                    pass

            headers = {"User-Agent": ua}
            req = urllib.request.Request(url, headers=headers)
            response = opener.open(req, timeout=30) if opener else urllib.request.urlopen(req, timeout=30)

            ct = response.headers.get("Content-Type", "").lower()
            is_html = ct.startswith("text/html")
            if is_html:
                logger.info(f"HTML page detected, scraping for audio sources: {url}")
                return self.scrape_and_download(url, progress_callback=progress_callback, cancel_check=cancel_check)

            total = total or int(response.headers.get("Content-Length", 0))
            if total == 0:
                cr = response.headers.get("Content-Range", "")
                if "/" in cr:
                    total = int(cr.rsplit("/", 1)[1])
            unknown_total = total == 0
            if filename_hint:
                base = filename_hint.rsplit(".", 1)[0] if "." in filename_hint else filename_hint
                ext = self._ext_for_ct(ct)
                filename = f"{base}.{ext}" if ext else filename_hint
            else:
                filename = self._get_filename(url, response)
            subfolder = subfolder_hint or get_subfolder(filename)
            dest_dir = os.path.join(self.download_path, subfolder)
            os.makedirs(dest_dir, exist_ok=True)
            filepath = os.path.join(dest_dir, filename)

            existing_size = 0
            if os.path.exists(filepath):
                existing_size = os.path.getsize(filepath)
                if total > 0 and existing_size == total:
                    if progress_callback:
                        progress_callback(f"[download] {filepath} has already been downloaded\n")
                    return True
                elif total > 0 and existing_size < total:
                    response.close()
                    headers["Range"] = f"bytes={existing_size}-"
                    req = urllib.request.Request(url, headers=headers)
                    try:
                        response = opener.open(req, timeout=30) if opener else urllib.request.urlopen(req, timeout=30)
                        total = existing_size + int(response.headers.get("Content-Length", 0))
                    except urllib.error.HTTPError as e:
                        if e.code == 416:
                            existing_size = 0
                            req = urllib.request.Request(url, headers={"User-Agent": headers["User-Agent"]})
                            response = opener.open(req, timeout=30) if opener else urllib.request.urlopen(req, timeout=30)
                            total = int(response.headers.get("Content-Length", 0))
                        else:
                            raise

            if progress_callback:
                progress_callback(f"Destination: {filepath}\n")

            downloaded = existing_size
            chunk_size = 65536
            last_pct = -1
            start_time = time.time()
            last_report_time = start_time
            last_report_bytes = downloaded

            mode = "ab" if existing_size > 0 else "wb"
            with open(filepath, mode) as f:
                while True:
                    if cancel_check and cancel_check():
                        f.close()
                        raise Exception("CANCELLED")

                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_report_time >= 0.5:
                        elapsed = now - start_time
                        elapsed_since_report = now - last_report_time
                        delta_bytes = downloaded - last_report_bytes
                        speed = delta_bytes / elapsed_since_report if elapsed_since_report > 0 else 0
                        last_report_time = now
                        last_report_bytes = downloaded

                        if unknown_total:
                            pct = 0.0
                            size_str = self._format_size(downloaded)
                            remaining = 0
                        else:
                            pct = round(downloaded / total * 100, 1)
                            size_str = self._format_size(total)
                            remaining = total - downloaded
                        eta_str = ""
                        if speed > 0 and remaining > 0:
                            eta_sec = int(remaining / speed)
                            if eta_sec >= 3600:
                                eta_str = f"{eta_sec // 3600}:{(eta_sec % 3600) // 60:02d}:{eta_sec % 60:02d}"
                            else:
                                eta_str = f"{eta_sec // 60}:{eta_sec % 60:02d}"

                        if progress_callback:
                            if unknown_total:
                                progress_callback("progress_mode: indeterminate\n")
                            progress_callback(
                                f"{pct:.1f}% of {size_str} at {self._format_size(speed)}/s"
                                + (f" ETA {eta_str}" if eta_str else "")
                                + "\n"
                            )

            logger.info(f"Direct download complete: {filepath}")
            return True

        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error downloading {url}: {e.code} {e.reason}")
            return False
        except Exception as e:
            logger.error(f"Direct download failed: {e}")
            if str(e) == "CANCELLED":
                raise
            return False

    @staticmethod
    def _format_size(bytes_val):
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"

    @staticmethod
    def _ext_for_ct(content_type):
        mapping = {
            "audio/mpeg": "mp3",
            "audio/mp4": "m4a",
            "audio/aac": "aac",
            "audio/ogg": "ogg",
            "audio/flac": "flac",
            "audio/wav": "wav",
            "audio/webm": "webm",
            "audio/x-m4a": "m4a",
            "audio/x-wav": "wav",
        }
        for ct_key, ext in mapping.items():
            if content_type.startswith(ct_key):
                return ext
        return None

    def scrape_and_download(self, url, progress_callback=None, cancel_check=None, stream_id=None):
        """Download HTML, extract audio sources, and download each found.

        If stream_id is given (e.g. "86747"), only download the stream URL
        whose /stream/{id}/ path matches.
        """
        if progress_callback:
            progress_callback("Scanning page for audio files...\n")

        cookie_jar = CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar)
        )

        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            req = urllib.request.Request(url, headers=headers)
            response = opener.open(req, timeout=30)
            html = response.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to fetch page for scraping: {e}")
            return False

        seen_urls = set()
        found_items = []
        def add_item(u, n, f):
            if u not in seen_urls:
                seen_urls.add(u)
                found_items.append((u, n, f))

        for m in re.finditer(r'<audio[^>]+src\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE):
            add_item(urllib.parse.urljoin(url, m.group(1)), None, None)
        for m in re.finditer(r'<source[^>]+src\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE):
            add_item(urllib.parse.urljoin(url, m.group(1)), None, None)
        for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+(' + "|".join(re.escape(e) for e in AUDIO_EXTS) + r'))["\']', html, re.IGNORECASE):
            add_item(urllib.parse.urljoin(url, m.group(1)), None, None)
        for m in re.finditer(r'["\']([^"\']+(' + "|".join(re.escape(e) for e in AUDIO_EXTS) + r'))["\']', html, re.IGNORECASE):
            add_item(urllib.parse.urljoin(url, m.group(1)), None, None)

        name_map = {}
        album_map = {}
        artist_map = {}
        for m in re.finditer(r"playlist\[(\d+)\]\.nomChanson\s*=\s*['\"]([^'\"]+)['\"]", html):
            name_map[int(m.group(1))] = clean_title(m.group(2))
        for m in re.finditer(r"playlist\[(\d+)\]\.album\s*=\s*['\"]([^'\"]+)['\"]", html):
            album_map[int(m.group(1))] = clean_title(m.group(2))
        for m in re.finditer(r"playlist\[(\d+)\]\.chanteur\s*=\s*['\"]([^'\"]+)['\"]", html):
            artist_map[int(m.group(1))] = clean_title(m.group(2))

        # Generic metadata extraction fallback
        generic_artist = None
        generic_album = None

        # 1. JSON-LD (schema.org)
        for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.IGNORECASE | re.DOTALL):
            try:
                import json
                data = json.loads(m.group(1))
                if isinstance(data, list):
                    data = data[0] if data else {}
                if isinstance(data, dict):
                    if data.get("@type") in ("MusicGroup", "MusicComposition", "Person"):
                        generic_artist = data.get("name") or generic_artist
                    if data.get("@type") == "MusicAlbum":
                        generic_album = data.get("name") or generic_album
                    if data.get("@type") == "MusicRecording":
                        by_artist = data.get("byArtist", {})
                        if isinstance(by_artist, dict):
                            generic_artist = by_artist.get("name") or generic_artist
                        elif isinstance(by_artist, list) and by_artist:
                            generic_artist = by_artist[0].get("name") or generic_artist
                        in_album = data.get("inAlbum", {})
                        if isinstance(in_album, dict):
                            generic_album = in_album.get("name") or generic_album
                        elif isinstance(in_album, list) and in_album:
                            generic_album = in_album[0].get("name") or generic_album
            except (json.JSONDecodeError, AttributeError):
                pass

        # 2. Open Graph / meta tags
        if not generic_artist:
            for m in re.finditer(r'<meta\s[^>]*?(?:property|name)=["\'](?:og:)?(?:author|artist|music:artist)["\'][^>]*?content=["\']([^"\']+)["\']', html, re.IGNORECASE):
                generic_artist = m.group(1).strip()
                break
        if not generic_artist:
            for m in re.finditer(r'<meta\s[^>]*?name=["\']author["\'][^>]*?content=["\']([^"\']+)["\']', html, re.IGNORECASE):
                generic_artist = m.group(1).strip()
                break
        if not generic_album:
            for m in re.finditer(r'<meta\s[^>]*?(?:property|name)=["\'](?:og:)?(?:album|music:album)["\'][^>]*?content=["\']([^"\']+)["\']', html, re.IGNORECASE):
                generic_album = m.group(1).strip()
                break

        # 3. <title> tag — try to extract "Artist - Song" or "Artist - Album"
        if not generic_artist or not generic_album:
            title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                for sep in [" - ", " | ", " — ", " – "]:
                    if sep in title:
                        parts = title.split(sep)
                        if not generic_artist:
                            generic_artist = parts[0].strip()
                        if not generic_album and len(parts) > 1:
                            candidate = parts[1].strip()
                            if len(candidate) > 2 and candidate.lower() not in ("download", "listen", "free", "mp3", "music", "audio", "online", "stream"):
                                generic_album = candidate
                        break
                if not generic_artist:
                    by_match = re.search(r'(?:by|de|par)\s+(.+?)(?:\s*[|—-]|\s*$)', title, re.IGNORECASE)
                    if by_match:
                        generic_artist = by_match.group(1).strip()
                if not generic_artist and len(title) < 50 and "audio" not in title.lower() and "music" not in title.lower():
                    generic_artist = title

        # 4. <h1> as artist fallback
        if not generic_artist:
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
            if h1_match:
                generic_artist = h1_match.group(1).strip()

        # 5. URL-derived album name (last meaningful path segment)
        if not generic_album:
            path_parts = [p for p in url.rstrip("/").split("/") if p and not p.startswith("#")]
            if path_parts:
                candidate = path_parts[-1].replace("-", " ").replace("_", " ").title()
                if len(candidate) > 2 and candidate.lower() not in ("en", "ar", "fr", "artist", "album", "song", "music", "audio", "download"):
                    generic_album = candidate

        # Clean all extracted metadata
        generic_artist = clean_title(generic_artist) if generic_artist else None
        generic_album = clean_title(generic_album) if generic_album else None

        # Apply generic metadata to items without site-specific data
        def apply_folder(song_idx, song_name, audio_url):
            ng_artist = artist_map.get(song_idx)
            ng_album = album_map.get(song_idx)
            ng_name = name_map.get(song_idx)
            artist = ng_artist or generic_artist
            album = ng_album or (generic_album if not ng_artist else None)
            folder = artist or album
            return (audio_url, ng_name or song_name or None, folder or None)

        for m in re.finditer(r"playlist\[(\d+)\]\.lien\s*=\s*['\"]([^'\"]+)['\"]", html):
            audio_url = urllib.parse.urljoin(url, m.group(2))
            song_index = int(m.group(1))
            add_item(*apply_folder(song_index, None, audio_url))
        for m in re.finditer(r'["\']((?:https?://[^"\'/]+)?/stream/[^"\']+)["\']', html, re.IGNORECASE):
            add_item(urllib.parse.urljoin(url, m.group(1)), None, None)

        # Fill generic folder for items without site-specific folder
        if generic_artist or generic_album:
            generic_folder = generic_artist or generic_album
            found_items[:] = [(u, n, f or generic_folder) for u, n, f in found_items]

        if not found_items:
            logger.warning(f"No audio sources found in page: {url}")
            return False

        logger.info(f"Found {len(found_items)} audio source(s) in page: {url}")
        total = len(found_items)
        if progress_callback:
            progress_callback(f"Downloading {total} audio items\n")

        success = False
        for i, (audio_url, hint, folder_hint) in enumerate(found_items):
            if cancel_check and cancel_check():
                break

            # If stream_id set, skip items that don't match
            if stream_id is not None:
                stream_match = re.search(r"/stream/" + re.escape(stream_id) + r"/", audio_url)
                if not stream_match:
                    continue

            label = clean_title(hint) or audio_url
            if progress_callback:
                progress_callback(f"[download] Downloading audio file {i+1} of {total}\n")
                progress_callback(f"[{i+1}/{total}] {label}\n")
            filename_hint = f"{hint}.mp3" if hint else None
            if self.download(audio_url, progress_callback=progress_callback, cancel_check=cancel_check, opener=opener, filename_hint=filename_hint, subfolder_hint=folder_hint):
                success = True

        if stream_id is not None and not success:
            logger.warning(f"stream_id {stream_id} not found in scraped page")
        return success
