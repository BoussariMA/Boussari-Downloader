import sys
import os
from downloader import YtDownloader
from config import QUALITY_TEMPLATES

def main():
    print("--- Linux Video Downloader (yt-dlp Wrapper) ---")
    
    url = input("Enter URL: ").strip()
    if not url:
        print("URL is required.")
        return

    download_path = input("Enter download directory [Default: ./downloads]: ").strip()
    if not download_path:
        download_path = os.path.join(os.getcwd(), "downloads")

    print("\nSelect Quality Mode:")
    modes = list(QUALITY_TEMPLATES.keys())
    for i, mode in enumerate(modes, 1):
        print(f"{i}. {QUALITY_TEMPLATES[mode]['description']}")
    
    try:
        choice = int(input("Choice (1-3): "))
        mode = modes[choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Using 'best' by default.")
        mode = "best"

    scope_choice = input("\nDownload whole playlist? (y/n) [Default: y]: ").strip().lower()
    is_playlist = scope_choice != 'n'

    print("\nStarting download...")
    downloader = YtDownloader(download_path)
    success = downloader.download(url, mode, is_playlist)

    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Failed. Check logs for details.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        sys.exit(0)
