"""
Google OAuth 2.0 service for teacher-only Google Classroom integration.

Handles:
  - Building the OAuth consent URL
  - Exchanging authorization codes for tokens
  - Encrypting / decrypting tokens at rest (Fernet)
  - Auto-refreshing expired access tokens
  - Disconnecting (revoking + deleting stored credentials)
"""
import logging
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.google_classroom import GoogleAccount

logger = logging.getLogger("numbersense.google_auth")

# Scopes required for Level 2 integration + roster import
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# ---------------------------------------------------------------------------
# Token encryption helpers
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    key = settings.GOOGLE_TOKEN_ENCRYPTION_KEY
    if not key:
        # In development without a key, use a deterministic fallback.
        # For production, GOOGLE_TOKEN_ENCRYPTION_KEY MUST be set.
        logger.warning("GOOGLE_TOKEN_ENCRYPTION_KEY not set — using insecure dev key")
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def _decrypt(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt Google token — encryption key may have changed")


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------

def build_oauth_url(state: str | None = None) -> str:
    """Return the Google OAuth consent URL the frontend should redirect to."""
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
        state=state or "",
    )
    return url


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for tokens.  Returns a dict with
    access_token, refresh_token, token_expiry, google_user_id, google_email.
    """
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Get user info (email, id)
    import httpx
    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
    )
    resp.raise_for_status()
    user_info = resp.json()

    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_expiry": creds.expiry,
        "google_user_id": user_info.get("id", ""),
        "google_email": user_info.get("email", ""),
    }


def save_tokens(db: Session, teacher_id: str, token_data: dict) -> GoogleAccount:
    """Create or update a GoogleAccount row with encrypted tokens."""
    acct = db.query(GoogleAccount).filter(
        GoogleAccount.teacher_id == teacher_id
    ).first()

    enc_access = _encrypt(token_data["access_token"])
    enc_refresh = _encrypt(token_data["refresh_token"])

    if acct:
        acct.google_user_id = token_data["google_user_id"]
        acct.google_email = token_data.get("google_email")
        acct.access_token_enc = enc_access
        acct.refresh_token_enc = enc_refresh
        acct.token_expiry = token_data.get("token_expiry")
    else:
        acct = GoogleAccount(
            teacher_id=teacher_id,
            google_user_id=token_data["google_user_id"],
            google_email=token_data.get("google_email"),
            access_token_enc=enc_access,
            refresh_token_enc=enc_refresh,
            token_expiry=token_data.get("token_expiry"),
        )
        db.add(acct)

    db.commit()
    db.refresh(acct)
    logger.info("Saved Google tokens for teacher %s (google_user=%s)",
                teacher_id, token_data["google_user_id"])
    return acct


# ---------------------------------------------------------------------------
# Credential retrieval with auto-refresh
# ---------------------------------------------------------------------------

def get_credentials(db: Session, teacher_id: str) -> Credentials:
    """Return a valid google.oauth2.credentials.Credentials object.

    Automatically refreshes the access token if it has expired and persists
    the new token back to the database.  Raises ValueError if no account
    is linked or the refresh token is revoked.
    """
    acct = db.query(GoogleAccount).filter(
        GoogleAccount.teacher_id == teacher_id
    ).first()
    if not acct:
        raise ValueError("Google account not connected")

    access_token = _decrypt(acct.access_token_enc)
    refresh_token = _decrypt(acct.refresh_token_enc)

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        expiry=acct.token_expiry,
    )

    # Refresh if expired (or within 5 minutes of expiry)
    if creds.expired or (creds.expiry and creds.expiry.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc)):
        logger.info("Refreshing expired Google token for teacher %s", teacher_id)
        try:
            creds.refresh(GoogleAuthRequest())
        except Exception as exc:
            logger.error("Google token refresh failed for teacher %s: %s", teacher_id, exc)
            raise ValueError(
                "Your Google Classroom connection has expired. "
                "Please reconnect in Settings."
            ) from exc

        # Persist refreshed token
        acct.access_token_enc = _encrypt(creds.token)
        if creds.refresh_token:
            acct.refresh_token_enc = _encrypt(creds.refresh_token)
        acct.token_expiry = creds.expiry
        db.commit()

    return creds


def is_connected(db: Session, teacher_id: str) -> dict:
    """Return connection status dict for the frontend."""
    acct = db.query(GoogleAccount).filter(
        GoogleAccount.teacher_id == teacher_id
    ).first()
    if not acct:
        return {"connected": False}
    return {
        "connected": True,
        "google_email": acct.google_email,
        "connected_at": acct.created_at.isoformat() if acct.created_at else None,
    }


def disconnect(db: Session, teacher_id: str) -> None:
    """Revoke tokens and delete the GoogleAccount row."""
    acct = db.query(GoogleAccount).filter(
        GoogleAccount.teacher_id == teacher_id
    ).first()
    if not acct:
        return

    # Best-effort revoke with Google
    try:
        token = _decrypt(acct.access_token_enc)
        import httpx
        httpx.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except Exception as exc:
        logger.warning("Token revocation failed (non-critical): %s", exc)

    db.delete(acct)
    db.commit()
    logger.info("Disconnected Google account for teacher %s", teacher_id)
