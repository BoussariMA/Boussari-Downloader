import threading
from downloader import YtDownloader, DirectDownloader
from logger import logger


class DownloadManager:
    def __init__(self):
        self._download_cancel = {}
        self._threads = {}

    def register_item(self, item_id):
        self._download_cancel[item_id] = threading.Event()

    def unregister_item(self, item_id):
        self._download_cancel.pop(item_id, None)

    def get_cancel_event(self, item_id):
        return self._download_cancel.get(item_id)

    def is_cancelled(self, item_id):
        ev = self._download_cancel.get(item_id)
        return ev is not None and ev.is_set()

    def launch(self, item_id, snapshots, on_downloading=None, on_progress=None, on_completed=None, on_error=None):
        cancel_ev = self._download_cancel.get(item_id)
        thread = threading.Thread(
            target=self._run,
            args=(item_id, snapshots, cancel_ev, on_downloading, on_progress, on_completed, on_error),
            daemon=True
        )
        self._threads[item_id] = thread
        thread.start()
        return thread

    def _run(self, item_id, snapshots, cancel_ev, on_downloading, on_progress, on_completed, on_error):
        dl_path = snapshots["download_path"]
        url = snapshots["url"]
        mode = snapshots["mode"]

        if on_downloading:
            on_downloading()

        try:
            if mode == "download_all":
                downloader = DirectDownloader(dl_path)
                success = downloader.scrape_and_download(
                    url,
                    progress_callback=on_progress,
                    cancel_check=lambda: cancel_ev.is_set() if cancel_ev else False
                )
            elif mode.startswith("download_single_id:"):
                stream_id = mode.split(":", 1)[1]
                downloader = DirectDownloader(dl_path)
                success = downloader.scrape_and_download(
                    url,
                    progress_callback=on_progress,
                    cancel_check=lambda: cancel_ev.is_set() if cancel_ev else False,
                    stream_id=stream_id
                )
            else:
                downloader = YtDownloader(dl_path)
                success = downloader.download(
                    url, mode, snapshots["is_playlist"],
                    cookie_source=snapshots["cookie_source"],
                    cookie_path=snapshots["cookie_path"],
                    flatpak_browser=snapshots["flatpak_browser"],
                    progress_callback=on_progress,
                    cancel_check=lambda: cancel_ev.is_set() if cancel_ev else False
                )
            if success:
                if on_completed:
                    on_completed(snapshots)
            else:
                if not (cancel_ev and cancel_ev.is_set()) and on_error:
                    on_error()
        except Exception as e:
            if cancel_ev and cancel_ev.is_set():
                return
            logger.error(f"Download thread error for {item_id}: {e}")
            if on_error:
                on_error()
        finally:
            self.unregister_item(item_id)
            self._threads.pop(item_id, None)

    def pause(self, item_id):
        ev = self._download_cancel.get(item_id)
        if ev:
            ev.set()

    def cancel(self, item_id):
        ev = self._download_cancel.get(item_id)
        if ev:
            ev.set()
        self.unregister_item(item_id)

    def cancel_all(self):
        for ev in self._download_cancel.values():
            ev.set()
        for t in list(self._threads.values()):
            if t.is_alive():
                t.join(timeout=2.0)
