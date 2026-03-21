"""Google Workspace integration for SmithAI.

Provides:
- Gmail: Send/manage emails
- Calendar: Events and scheduling
- Drive: File management
- Sheets: Spreadsheet operations
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class GoogleConfig:
    credentials_path: Optional[str] = None
    token_path: str = "token.json"
    
    @classmethod
    def from_env(cls) -> "GoogleConfig":
        return cls(
            credentials_path=os.environ.get("GOOGLE_CREDENTIALS_PATH"),
            token_path=os.environ.get("GOOGLE_TOKEN_PATH", "token.json"),
        )


class GoogleWorkspace:
    """Google Workspace API client.
    
    Real use cases:
    - Send reports via email
    - Schedule meetings
    - Manage calendar
    - Access Drive files
    - Update spreadsheets
    """
    
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/drive",
    ]
    
    def __init__(self, config: Optional[GoogleConfig] = None):
        self.config = config or GoogleConfig.from_env()
        self._access_token: Optional[str] = None
        self._credentials = None
    
    def authenticate(self) -> bool:
        """Authenticate with Google."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            if os.path.exists(self.config.token_path):
                self._credentials = Credentials.from_authorized_user_file(
                    self.config.token_path, self.SCOPES
                )
            elif self.config.credentials_path and os.path.exists(self.config.credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.credentials_path, self.SCOPES
                )
                self._credentials = flow.run_local_server(port=0)
                with open(self.config.token_path, "w") as f:
                    self._credentials.to_json(f)
            else:
                return False
            
            self._access_token = self._credentials.token
            return True
        except Exception:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}


class GmailTool(GoogleWorkspace):
    """Gmail API operations."""
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an email."""
        if not httpx or not self._access_token:
            return {"success": False, "error": "Not authenticated"}
        
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc
        
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers=self._get_headers(),
                json={"raw": encoded}
            )
            return response.json()
    
    async def get_emails(
        self,
        query: str = "",
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get emails matching query."""
        if not httpx or not self._access_token:
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers=self._get_headers(),
                params={"q": query, "maxResults": max_results}
            )
            data = response.json()
            return data.get("messages", [])
    
    async def get_email(self, message_id: str) -> Dict[str, Any]:
        """Get email by ID."""
        if not httpx or not self._access_token:
            return {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                headers=self._get_headers()
            )
            return response.json()


class CalendarTool(GoogleWorkspace):
    """Google Calendar API operations."""
    
    async def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a calendar event."""
        if not httpx or not self._access_token:
            return {}
        
        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }
        
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=self._get_headers(),
                json=event
            )
            return response.json()
    
    async def get_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get upcoming events."""
        if not httpx or not self._access_token:
            return []
        
        params = {"maxResults": max_results}
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=self._get_headers(),
                params=params
            )
            data = response.json()
            return data.get("items", [])
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        if not httpx or not self._access_token:
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                headers=self._get_headers()
            )
            return response.status_code == 204


class DriveTool(GoogleWorkspace):
    """Google Drive API operations."""
    
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        query: str = "",
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """List files in Drive."""
        if not httpx or not self._access_token:
            return []
        
        params = {
            "pageSize": max_results,
            "fields": "files(id,name,mimeType,webViewLink,createdTime,modifiedTime)",
        }
        
        if folder_id:
            params["q"] = f"'{folder_id}' in parents and trashed = false"
        elif query:
            params["q"] = query
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=self._get_headers(),
                params=params
            )
            data = response.json()
            return data.get("files", [])
    
    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a folder."""
        if not httpx or not self._access_token:
            return {}
        
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        
        if parent_id:
            file_metadata["parents"] = [parent_id]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/drive/v3/files",
                headers=self._get_headers(),
                json=file_metadata
            )
            return response.json()
    
    async def upload_file(
        self,
        name: str,
        content: bytes,
        parent_id: Optional[str] = None,
        mime_type: str = "text/plain",
    ) -> Dict[str, Any]:
        """Upload a file."""
        if not httpx or not self._access_token:
            return {}
        
        from httpx import DataField
        
        file_metadata = {"name": name}
        if parent_id:
            file_metadata["parents"] = [parent_id]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/upload/drive/v3/files",
                headers={
                    **self._get_headers(),
                    "Content-Type": "multipart/related",
                },
                data={
                    "metadata": (None, str(file_metadata), "application/json"),
                    "file": (name, content, mime_type),
                }
            )
            return response.json()


__all__ = ["GoogleWorkspace", "GoogleConfig", "GmailTool", "CalendarTool", "DriveTool"]
