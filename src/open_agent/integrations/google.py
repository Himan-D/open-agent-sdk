"""Google Workspace integration - Official Google APIs.

Real API integration with Google Workspace using official google-api-python-client,
google-auth, and google-oauthlib libraries. Matches OpenClaw's Google integration.
"""

import os
import asyncio
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
from pathlib import Path
import json
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class GoogleOAuthConfig:
    """Google OAuth2 configuration."""
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8080/oauth/callback"
    scopes: List[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/calendar.readonly",
                "https://www.googleapis.com/auth/calendar.events",
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/drive.file",
            ]


@dataclass
class GoogleTokens:
    """OAuth tokens storage."""
    token: str = ""
    refresh_token: str = ""
    token_uri: str = "https://oauth2.googleapis.com/token"
    client_id: str = ""
    client_secret: str = ""
    scopes: List[str] = None
    expiry: float = 0


class GoogleOAuthFlow:
    """Google OAuth2 authentication flow - matches OpenClaw implementation."""

    def __init__(self, config: GoogleOAuthConfig):
        self.config = config
        self._flow = None
        self._creds = None

    def get_authorization_url(self) -> tuple[str, str]:
        """Get authorization URL and state token."""
        try:
            from google_auth_oauthlib.flow import Flow

            self._flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "redirect_uris": [self.config.redirect_uri],
                    }
                },
                scopes=self.config.scopes,
            )
            self._flow.redirect_uri = self.config.redirect_uri

            auth_url, state = self._flow.authorization_url(
                access_type="offline",
                prompt="consent",
                include_granted_scopes="true",
            )

            logger.info("google_auth_url_generated")
            return auth_url, state

        except ImportError as e:
            logger.error("google_auth_libs_missing", error=str(e))
            raise ImportError(
                "Install Google auth libraries: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )

    def fetch_token(self, authorization_response: str) -> bool:
        """Exchange authorization code for tokens."""
        if not self._flow:
            logger.error("google_auth_flow_not_started")
            return False

        try:
            self._flow.fetch_token(authorization_response=authorization_response)
            self._creds = self._flow.credentials
            logger.info("google_token_fetched")
            return True
        except Exception as e:
            logger.error("google_token_fetch_failed", error=str(e))
            return False

    def save_tokens(self, path: str = "~/.open-agent/google_tokens.json") -> bool:
        """Save tokens to file."""
        if not self._creds:
            return False

        try:
            token_path = Path(path).expanduser()
            token_path.parent.mkdir(parents=True, exist_ok=True)

            tokens = {
                "token": self._creds.token,
                "refresh_token": self._creds.refresh_token,
                "token_uri": self._creds.token_uri,
                "client_id": self._creds.client_id,
                "client_secret": self._creds.client_secret,
                "scopes": self._creds.scopes,
                "expiry": self._creds.expiry.timestamp() if self._creds.expiry else 0,
            }

            token_path.write_text(json.dumps(tokens, indent=2))
            logger.info("google_tokens_saved", path=str(token_path))
            return True

        except Exception as e:
            logger.error("google_tokens_save_failed", error=str(e))
            return False

    def load_tokens(self, path: str = "~/.open-agent/google_tokens.json") -> bool:
        """Load tokens from file."""
        try:
            token_path = Path(path).expanduser()
            if not token_path.exists():
                logger.warning("google_tokens_file_not_found")
                return False

            data = json.loads(token_path.read_text())
            
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            self._creds = Credentials(
                token=data.get("token"),
                refresh_token=data.get("refresh_token"),
                token_uri=data.get("token_uri"),
                client_id=data.get("client_id"),
                client_secret=data.get("client_secret"),
                scopes=data.get("scopes"),
            )

            # Check if expired and refresh
            if self._creds.expired and self._creds.refresh_token:
                self._creds.refresh(Request())
                self.save_tokens(path)

            logger.info("google_tokens_loaded")
            return True

        except Exception as e:
            logger.error("google_tokens_load_failed", error=str(e))
            return False

    @property
    def credentials(self):
        """Get credentials."""
        return self._creds

    def is_valid(self) -> bool:
        """Check if credentials are valid."""
        return self._creds is not None and self._creds.valid


class GoogleServices:
    """Google Workspace services - matches OpenClaw's google tool."""

    def __init__(self, oauth_flow: GoogleOAuthFlow):
        self.oauth = oauth_flow
        self._services: Dict[str, Any] = {}

    def _get_service(self, name: str, version: str, build_fn: Callable):
        """Get or create a service."""
        key = f"{name}_{version}"
        if key not in self._services:
            self._services[key] = build_fn(self.oauth.credentials)
        return self._services[key]

    @property
    def gmail(self):
        """Get Gmail service."""
        from googleapiclient.discovery import build
        return self._get_service("gmail", "v1", lambda creds: build("gmail", "v1", credentials=creds, static_discovery=False))

    @property
    def calendar(self):
        """Get Calendar service."""
        from googleapiclient.discovery import build
        return self._get_service("calendar", "v3", lambda creds: build("calendar", "v3", credentials=creds, static_discovery=False))

    @property
    def drive(self):
        """Get Drive service."""
        from googleapiclient.discovery import build
        return self._get_service("drive", "v3", lambda creds: build("drive", "v3", credentials=creds, static_discovery=False))

    @property
    def sheets(self):
        """Get Sheets service."""
        from googleapiclient.discovery import build
        return self._get_service("sheets", "v4", lambda creds: build("sheets", "v4", credentials=creds, static_discovery=False))

    @property
    def docs(self):
        """Get Docs service."""
        from googleapiclient.discovery import build
        return self._get_service("docs", "v1", lambda creds: build("docs", "v1", credentials=creds, static_discovery=False))

    @property
    def searchconsole(self):
        """Get Search Console service."""
        from googleapiclient.discovery import build
        return self._get_service("searchconsole", "v1", lambda creds: build("searchconsole", "v1", credentials=creds, static_discovery=False))


class GmailTool:
    """Gmail tool - matches OpenClaw's gmail tool."""

    def __init__(self, services: GoogleServices):
        self.services = services

    async def list_emails(self, query: str = "", max_results: int = 10) -> List[Dict]:
        """List emails matching query."""
        try:
            results = (
                self.services.gmail.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = []
            for msg in results.get("messages", []):
                msg_data = (
                    self.services.gmail.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="metadata")
                    .execute()
                )

                headers = msg_data.get("payload", {}).get("headers", [])
                
                def get_header(name):
                    for h in headers:
                        if h["name"].lower() == name.lower():
                            return h["value"]
                    return ""

                messages.append({
                    "id": msg["id"],
                    "from": get_header("From"),
                    "to": get_header("To"),
                    "subject": get_header("Subject"),
                    "date": get_header("Date"),
                    "snippet": msg_data.get("snippet", ""),
                })

            return messages

        except Exception as e:
            logger.error("gmail_list_failed", error=str(e))
            return []

    async def send_email(self, to: str, subject: str, body: str) -> Dict:
        """Send an email."""
        try:
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.multipart import MIMEBase
            import email.encoders

            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject
            message.attach(MIMEText(body, "plain"))

            encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = (
                self.services.gmail.users()
                .messages()
                .send(userId="me", body={"raw": encoded})
                .execute()
            )

            return {"success": True, "message_id": result["id"]}

        except Exception as e:
            logger.error("gmail_send_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_email(self, message_id: str) -> Optional[Dict]:
        """Get full email content."""
        try:
            msg = (
                self.services.gmail.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = msg.get("payload", {}).get("headers", [])
            
            def get_header(name):
                for h in headers:
                    if h["name"].lower() == name.lower():
                        return h["value"]
                return ""

            # Get body
            body = ""
            parts = msg.get("payload", {}).get("parts", [])
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        import base64
                        body = base64.urlsafe_b64decode(data).decode()

            return {
                "id": msg["id"],
                "from": get_header("From"),
                "to": get_header("To"),
                "subject": get_header("Subject"),
                "date": get_header("Date"),
                "body": body,
                "snippet": msg.get("snippet", ""),
            }

        except Exception as e:
            logger.error("gmail_get_failed", error=str(e))
            return None


class CalendarTool:
    """Calendar tool - matches OpenClaw's google calendar tool."""

    def __init__(self, services: GoogleServices):
        self.services = services

    async def list_events(
        self,
        days: int = 7,
        max_results: int = 50,
    ) -> List[Dict]:
        """List upcoming events."""
        try:
            from datetime import datetime, timedelta

            now = datetime.utcnow()
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(days=days)).isoformat() + "Z"

            events = (
                self.services.calendar.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            return [
                {
                    "id": e.get("id"),
                    "summary": e.get("summary", "No title"),
                    "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date")),
                    "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date")),
                    "location": e.get("location", ""),
                    "description": e.get("description", ""),
                    "attendees": [a.get("email") for a in e.get("attendees", [])],
                }
                for e in events.get("items", [])
            ]

        except Exception as e:
            logger.error("calendar_list_failed", error=str(e))
            return []

    async def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        description: str = "",
        location: str = "",
        attendees: Optional[List[str]] = None,
    ) -> Dict:
        """Create a calendar event."""
        try:
            event = {
                "summary": summary,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"},
                "description": description,
                "location": location,
            }

            if attendees:
                event["attendees"] = [{"email": a} for a in attendees]

            result = (
                self.services.calendar.events()
                .insert(calendarId="primary", body=event)
                .execute()
            )

            return {"success": True, "event_id": result["id"], "link": result.get("htmlLink")}

        except Exception as e:
            logger.error("calendar_create_failed", error=str(e))
            return {"success": False, "error": str(e)}


class DriveTool:
    """Drive tool - matches OpenClaw's google drive tool."""

    def __init__(self, services: GoogleServices):
        self.services = services

    async def list_files(self, folder_id: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """List files in Drive."""
        try:
            query = f"'{folder_id or 'root'}' in parents and trashed = false"
            
            results = (
                self.services.drive.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id, name, mimeType, modifiedTime, webViewLink, shared)",
                )
                .execute()
            )

            return [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "type": f.get("mimeType"),
                    "modified": f.get("modifiedTime"),
                    "link": f.get("webViewLink"),
                    "shared": f.get("shared"),
                }
                for f in results.get("files", [])
            ]

        except Exception as e:
            logger.error("drive_list_failed", error=str(e))
            return []

    async def search_files(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search files by name."""
        try:
            results = (
                self.services.drive.files()
                .list(
                    q=f"name contains '{query}' and trashed = false",
                    pageSize=max_results,
                    fields="files(id, name, mimeType, modifiedTime)",
                )
                .execute()
            )

            return [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "type": f.get("mimeType"),
                    "modified": f.get("modifiedTime"),
                }
                for f in results.get("files", [])
            ]

        except Exception as e:
            logger.error("drive_search_failed", error=str(e))
            return []

    async def read_file(self, file_id: str) -> Optional[str]:
        """Read file content."""
        try:
            result = (
                self.services.drive.files()
                .get_media(fileId=file_id)
                .execute()
            )
            return result.decode() if isinstance(result, bytes) else result

        except Exception as e:
            logger.error("drive_read_failed", error=str(e))
            return None

    async def create_file(self, name: str, content: str, folder_id: Optional[str] = None) -> Dict:
        """Create a new file."""
        try:
            import base64

            file_metadata = {"name": name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = type("Media", (), {
                "mimetype": "text/plain",
                "body": content,
            })()

            result = (
                self.services.drive.files()
                .create(body=file_metadata, media_body=media, fields="id, webViewLink")
                .execute()
            )

            return {"success": True, "file_id": result["id"], "link": result.get("webViewLink")}

        except Exception as e:
            logger.error("drive_create_failed", error=str(e))
            return {"success": False, "error": str(e)}


class GoogleWorkspace:
    """Full Google Workspace integration - matches OpenClaw."""

    def __init__(self, oauth_flow: Optional[GoogleOAuthFlow] = None):
        self.oauth = oauth_flow or GoogleOAuthFlow(GoogleOAuthConfig())
        self.services = GoogleServices(self.oauth)
        
        self.gmail = GmailTool(self.services)
        self.calendar = CalendarTool(self.services)
        self.drive = DriveTool(self.services)

    def get_auth_url(self) -> tuple[str, str]:
        """Get OAuth authorization URL."""
        return self.oauth.get_authorization_url()

    def complete_auth(self, authorization_response: str) -> bool:
        """Complete OAuth flow."""
        if self.oauth.fetch_token(authorization_response):
            return self.oauth.save_tokens()
        return False

    def load_from_file(self, path: str = "~/.open-agent/google_tokens.json") -> bool:
        """Load credentials from file."""
        return self.oauth.load_tokens(path)

    def save_to_file(self, path: str = "~/.open-agent/google_tokens.json") -> bool:
        """Save credentials to file."""
        return self.oauth.save_tokens(path)

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.oauth.is_valid()


def create_google_workspace(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    credentials_file: Optional[str] = None,
) -> GoogleWorkspace:
    """Create Google Workspace instance.
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        credentials_file: Path to credentials.json file
    
    Returns:
        GoogleWorkspace instance
    """
    oauth_flow = None

    if credentials_file:
        # Load from credentials file
        try:
            import google_auth_oauthlib.flow
            oauth_flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                credentials_file,
                scopes=[
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/calendar.readonly",
                    "https://www.googleapis.com/auth/calendar.events",
                    "https://www.googleapis.com/auth/drive.readonly",
                    "https://www.googleapis.com/auth/drive.file",
                ],
            )
            # Create wrapper
            config = GoogleOAuthConfig(
                client_id=client_id or "",
                client_secret=client_secret or "",
            )
            oauth_flow = GoogleOAuthFlow(config)
        except Exception as e:
            logger.error("google_credentials_load_failed", error=str(e))

    if not oauth_flow:
        # Use provided or env credentials
        config = GoogleOAuthConfig(
            client_id=client_id or os.environ.get("GOOGLE_CLIENT_ID", ""),
            client_secret=client_secret or os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        )
        oauth_flow = GoogleOAuthFlow(config)

    workspace = GoogleWorkspace(oauth_flow)
    
    # Try to load from file
    workspace.load_from_file()
    
    return workspace
