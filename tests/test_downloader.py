import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from downloader import YtDownloader, DirectDownloader, is_direct_url


def test_is_direct_url():
    assert is_direct_url("https://example.com/file.mp4")
    assert is_direct_url("https://example.com/file.zip")
    assert is_direct_url("https://example.com/file.pdf")
    assert not is_direct_url("https://youtube.com/watch?v=abc123")
    assert not is_direct_url("https://example.com/path/to/page")
    print("[PASS] test_is_direct_url")


def test_build_command_best():
    dl = YtDownloader("/tmp/downloads")
    cmd = dl.build_command("https://youtube.com/watch?v=test", "best", is_playlist=False)
    assert "yt-dlp" in cmd[0]
    assert "-f" in cmd
    idx = cmd.index("-f")
    assert cmd[idx + 1] == "bv*+ba/b"
    assert "--no-playlist" in cmd
    assert "--yes-playlist" not in cmd
    print("[PASS] test_build_command_best")


def test_build_command_raw_format():
    dl = YtDownloader("/tmp/downloads")
    cmd = dl.build_command("https://youtube.com/watch?v=test", "22", is_playlist=False)
    idx = cmd.index("-f")
    assert cmd[idx + 1] == "22"
    print("[PASS] test_build_command_raw_format")


def test_build_command_playlist():
    dl = YtDownloader("/tmp/downloads")
    cmd = dl.build_command("https://youtube.com/playlist?list=test", "best", is_playlist=True)
    assert "--yes-playlist" in cmd
    assert "--no-playlist" not in cmd
    print("[PASS] test_build_command_playlist")


def test_build_command_cookies():
    dl = YtDownloader("/tmp/downloads")
    cmd = dl.build_command("https://youtube.com/watch?v=test", "best",
                          cookie_source="firefox")
    assert "--cookies-from-browser" in cmd
    idx = cmd.index("--cookies-from-browser")
    assert cmd[idx + 1] == "firefox"
    print("[PASS] test_build_command_cookies")


def test_format_size():
    assert DirectDownloader._format_size(0) == "0.0 B"
    assert DirectDownloader._format_size(1023) == "1023.0 B"
    assert DirectDownloader._format_size(1024) == "1.0 KB"
    assert DirectDownloader._format_size(1048576) == "1.0 MB"
    assert DirectDownloader._format_size(1073741824) == "1.0 GB"
    print("[PASS] test_format_size")


def test_direct_url_extensions():
    extensions = [".mp4", ".mkv", ".mp3", ".zip", ".pdf", ".jpg", ".png", ".exe", ".iso"]
    for ext in extensions:
        assert is_direct_url(f"https://example.com/file{ext}"), f"Failed for {ext}"
    print("[PASS] test_direct_url_extensions")


if __name__ == "__main__":
    test_is_direct_url()
    test_build_command_best()
    test_build_command_raw_format()
    test_build_command_playlist()
    test_build_command_cookies()
    test_format_size()
    test_direct_url_extensions()
    print("\n=== ALL TESTS PASSED ===")
