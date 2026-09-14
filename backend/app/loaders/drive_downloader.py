"""Google Drive public file downloader without Google Cloud API credentials."""

import re
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import gdown
import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import sanitize_filename

settings = get_settings()


def extract_drive_file_id(url: str) -> str:
    """Extract file ID from various Google Drive URL formats.

    Supported patterns:
    - https://drive.google.com/file/d/{FILE_ID}/view...
    - https://drive.google.com/open?id={FILE_ID}
    - https://drive.google.com/uc?id={FILE_ID}

    Args:
        url: Public Google Drive sharing link.

    Returns:
        Extracted file ID.

    Raises:
        HTTPException: If URL format is unrecognized.
    """
    url = url.strip()

    # Pattern 1: /file/d/<ID>/
    match = re.search(r"/file/d/([a-zA-Z0-9_-]{25,})", url)
    if match:
        return match.group(1)

    # Pattern 2: id=<ID> in query params
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    if "id" in query_params:
        file_id = query_params["id"][0]
        if re.match(r"^[a-zA-Z0-9_-]{25,}$", file_id):
            return file_id

    # Pattern 3: Bare ID check
    if re.match(r"^[a-zA-Z0-9_-]{25,}$", url):
        return url

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="URL de Google Drive inválida. Debe ser un enlace público a un archivo (ej: https://drive.google.com/file/d/.../view).",
    )


async def download_drive_file(url: str, output_dir: Path | None = None) -> Path:
    """Download a public Google Drive file using gdown with httpx fallback.

    Args:
        url: Public Google Drive link.
        output_dir: Destination folder. Defaults to settings.UPLOAD_DIR.

    Returns:
        Path to the downloaded local file.

    Raises:
        HTTPException: If download fails or file is inaccessible.
    """
    file_id = extract_drive_file_id(url)
    target_dir = output_dir or settings.UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    temp_filename = f"drive_{uuid.uuid4().hex[:8]}"
    destination_prefix = target_dir / temp_filename

    # Engine 1: gdown (handles virus scan warnings and large files)
    try:
        download_url = f"https://drive.google.com/uc?id={file_id}"
        output_path_str = gdown.download(
            url=download_url,
            output=str(destination_prefix),
            quiet=True,
            fuzzy=True,
        )
        if output_path_str and Path(output_path_str).exists():
            downloaded = Path(output_path_str)
            if downloaded.stat().st_size > 0:
                clean_name = sanitize_filename(downloaded.name)
                final_path = target_dir / f"drive_{uuid.uuid4().hex[:6]}_{clean_name}"
                downloaded.rename(final_path)
                return final_path
    except Exception:
        pass

    # Engine 2: Fallback with httpx streaming
    try:
        export_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            resp = await client.get(export_url)
            if resp.status_code == 200 and len(resp.content) > 0:
                # Determine extension from Content-Type or header
                content_disp = resp.headers.get("Content-Disposition", "")
                filename_match = re.search(r'filename="?([^"]+)"?', content_disp)
                raw_filename = filename_match.group(1) if filename_match else f"{temp_filename}.pdf"
                safe_name = sanitize_filename(raw_filename)
                target_file = target_dir / f"drive_{uuid.uuid4().hex[:6]}_{safe_name}"

                with open(target_file, "wb") as f:
                    f.write(resp.content)
                return target_file
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo descargar el archivo desde Google Drive: {exc}. Asegúrate de que el archivo tenga acceso 'Cualquiera con el enlace puede ver'.",
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Error al descargar archivo de Google Drive. Verifica que el enlace sea público.",
    )
