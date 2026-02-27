import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_MIME = "application/vnd.google-apps.folder"


def _load_credentials(credentials_path: str) -> Credentials:
    """Load OAuth2 user credentials, triggering browser login on first use.

    credentials_path: path to the OAuth client JSON downloaded from Google Cloud Console.
    A token.json file is saved next to it for subsequent runs.
    """
    token_path = Path(credentials_path).parent / "token.json"
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=5173)
        token_path.write_text(creds.to_json())
        logger.info("Google Drive token saved to %s", token_path)

    return creds


class GDriveService:
    """Google Drive API wrapper using OAuth2 user credentials."""

    def __init__(self, credentials_path: str):
        creds = _load_credentials(credentials_path)
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def _files(self):
        return self._service.files()

    def create_folder(self, name: str, parent_id: str) -> str:
        """Create a folder in Drive and return its ID."""
        metadata = {
            "name": name,
            "mimeType": FOLDER_MIME,
            "parents": [parent_id],
        }
        folder = self._files().create(body=metadata, fields="id").execute()
        return folder["id"]

    def get_or_create_folder(self, name: str, parent_id: str) -> str:
        """Find an existing folder by name under parent, or create one."""
        query = (
            f"name='{name}' and '{parent_id}' in parents "
            f"and mimeType='{FOLDER_MIME}' and trashed=false"
        )
        results = self._files().list(q=query, fields="files(id)", pageSize=1).execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]
        return self.create_folder(name, parent_id)

    def upload_file(
        self, local_path: Path, folder_id: str, drive_filename: str
    ) -> str:
        """Upload a file to Drive and return its ID."""
        metadata = {"name": drive_filename, "parents": [folder_id]}
        media = MediaFileUpload(str(local_path), mimetype="video/mp4", resumable=True)
        uploaded = (
            self._files().create(body=metadata, media_body=media, fields="id").execute()
        )
        logger.info("Uploaded %s → Drive (id=%s)", drive_filename, uploaded["id"])
        return uploaded["id"]

    def list_old_files(self, folder_id: str, older_than_days: int) -> list[dict]:
        """Recursively list video files older than N days under folder_id."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
        old_files: list[dict] = []

        # Find subfolders (camera folders)
        q = f"'{folder_id}' in parents and mimeType='{FOLDER_MIME}' and trashed=false"
        cam_folders = self._files().list(q=q, fields="files(id,name)").execute()

        for cam_folder in cam_folders.get("files", []):
            # Find date subfolders
            q2 = (
                f"'{cam_folder['id']}' in parents "
                f"and mimeType='{FOLDER_MIME}' and trashed=false"
            )
            date_folders = self._files().list(q=q2, fields="files(id,name)").execute()

            for date_folder in date_folders.get("files", []):
                # Find old video files in this date folder
                q3 = (
                    f"'{date_folder['id']}' in parents "
                    f"and mimeType!='{FOLDER_MIME}' and trashed=false "
                    f"and createdTime < '{cutoff_str}'"
                )
                videos = (
                    self._files()
                    .list(q=q3, fields="files(id,name)", pageSize=1000)
                    .execute()
                )
                old_files.extend(videos.get("files", []))

        return old_files

    def delete_file(self, file_id: str) -> None:
        """Delete a file from Drive."""
        self._files().delete(fileId=file_id).execute()

    def find_folder(self, name: str, parent_id: str) -> str | None:
        """Find a folder by name under parent. Returns ID or None."""
        query = (
            f"name='{name}' and '{parent_id}' in parents "
            f"and mimeType='{FOLDER_MIME}' and trashed=false"
        )
        results = self._files().list(q=query, fields="files(id)", pageSize=1).execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    def list_files_in_folder(self, folder_id: str) -> list[dict]:
        """List all non-folder files in a folder, returning name and id."""
        query = (
            f"'{folder_id}' in parents "
            f"and mimeType!='{FOLDER_MIME}' and trashed=false"
        )
        results = (
            self._files()
            .list(q=query, fields="files(id,name)", pageSize=1000, orderBy="name")
            .execute()
        )
        return results.get("files", [])

    def list_subfolders(self, parent_id: str) -> list[dict]:
        """List subfolder names under a parent folder."""
        query = (
            f"'{parent_id}' in parents "
            f"and mimeType='{FOLDER_MIME}' and trashed=false"
        )
        results = (
            self._files()
            .list(q=query, fields="files(id,name)", pageSize=1000, orderBy="name")
            .execute()
        )
        return results.get("files", [])

    def get_file_size(self, file_id: str) -> int:
        """Get file size in bytes."""
        metadata = self._files().get(fileId=file_id, fields="size").execute()
        return int(metadata["size"])

    def download_bytes(self, file_id: str, start: int = 0, end: int | None = None) -> bytes:
        """Download file bytes, optionally a specific range."""
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        headers = {}
        if end is not None:
            headers["Range"] = f"bytes={start}-{end}"
        _, content = self._service._http.request(url, headers=headers)
        return content
