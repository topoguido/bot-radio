import gc
import os
import uhashlib
import urequests


class Senko:
    raw = "https://raw.githubusercontent.com"
    github = "https://github.com"
    chunk_size = 512

    def __init__(
        self,
        user,
        repo,
        url=None,
        branch="master",
        working_dir="app",
        files=None,
        headers=None,
    ):
        """Senko OTA agent class."""
        self.base_url = (
            "{}/{}/{}".format(self.raw, user, repo)
            if user
            else url.replace(self.github, self.raw)
        )
        self.url = (
            url
            if url is not None
            else "{}/{}/{}".format(self.base_url, branch, working_dir)
        )
        self.headers = {} if headers is None else headers
        self.files = ["boot.py", "main.py"] if files is None else files

    @staticmethod
    def _remove(path):
        try:
            os.remove(path)
        except OSError:
            pass

    def _hash_file(self, path):
        try:
            local_file = open(path, "rb")
        except OSError:
            return None

        digest = uhashlib.sha1()
        buffer = bytearray(self.chunk_size)
        view = memoryview(buffer)

        try:
            while True:
                size = local_file.readinto(buffer)
                if not size:
                    break
                digest.update(view[:size])
        finally:
            local_file.close()

        return digest.digest()

    def _download_file(self, file):
        temporary = file + ".ota"
        response = None
        self._remove(temporary)

        try:
            response = urequests.get(
                self.url + "/" + file,
                headers=self.headers,
            )
            if response.status_code != 200:
                raise OSError(
                    "HTTP {} descargando {}".format(response.status_code, file)
                )

            digest = uhashlib.sha1()
            buffer = bytearray(self.chunk_size)
            view = memoryview(buffer)

            with open(temporary, "wb") as output:
                while True:
                    size = response.raw.readinto(buffer)
                    if not size:
                        break
                    chunk = view[:size]
                    digest.update(chunk)
                    output.write(chunk)

            return temporary, digest.digest()
        except Exception:
            self._remove(temporary)
            raise
        finally:
            if response is not None:
                response.close()
            gc.collect()

    def _stage_changes(self):
        changes = []

        for file in self.files:
            self._remove(file + ".ota")

        try:
            for file in self.files:
                gc.collect()
                temporary, remote_hash = self._download_file(file)
                local_hash = self._hash_file(file)

                if remote_hash == local_hash:
                    self._remove(temporary)
                else:
                    changes.append((file, temporary, local_hash is not None))
        except Exception:
            for file in self.files:
                self._remove(file + ".ota")
            raise

        return changes

    def _apply_changes(self, changes):
        applied = []

        try:
            for file, temporary, has_original in changes:
                backup = file + ".bak"
                self._remove(backup)

                if has_original:
                    os.rename(file, backup)

                try:
                    os.rename(temporary, file)
                except Exception:
                    if has_original:
                        os.rename(backup, file)
                    raise

                applied.append((file, backup, has_original))
        except Exception:
            for file, backup, has_original in reversed(applied):
                self._remove(file)
                if has_original:
                    os.rename(backup, file)

            for _, temporary, _ in changes:
                self._remove(temporary)
            raise

        for _, backup, has_original in applied:
            if has_original:
                self._remove(backup)

    def fetch(self):
        """Return True when at least one remote file differs."""
        changes = self._stage_changes()

        for _, temporary, _ in changes:
            self._remove(temporary)

        return bool(changes)

    def update(self):
        """Download and install changed files, returning whether any changed."""
        changes = self._stage_changes()

        if not changes:
            return False

        self._apply_changes(changes)
        gc.collect()
        return True
