"""Backup export (.ragpkg download) and restore routes."""

import uuid
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.backup.exporter import export_tenant_backup
from app.backup.importer import import_tenant_backup
from app.core.auth import TenantContext, get_tenant_context
from app.core.config import get_settings

router = APIRouter(prefix="/backup", tags=["Agnostic Backups (.ragpkg)"])
settings = get_settings()


@router.post(
    "/export",
    summary="Export knowledge base to portable .ragpkg file",
)
async def export_backup(tenant: TenantContext = Depends(get_tenant_context)):
    """Generate a portable compressed .ragpkg archive containing all documents, chunks and vectors."""
    backup_path = await export_tenant_backup(tenant.tenant_id)
    return FileResponse(
        path=str(backup_path),
        media_type="application/gzip",
        filename=backup_path.name,
    )


@router.post(
    "/import",
    summary="Restore knowledge base from a .ragpkg file",
)
async def import_backup(
    file: UploadFile,
    targets: str = Form("postgres", description="Target stores: postgres, mongo, both"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Restore documents, chunks and vectors from an uploaded .ragpkg package into current tenant memory."""
    if not file.filename or not file.filename.endswith(".ragpkg"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo inválido. El paquete de respaldo debe terminar en '.ragpkg'.",
        )

    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = settings.BACKUP_DIR / f"import_{uuid.uuid4().hex[:8]}_{file.filename}"

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar archivo de respaldo: {exc}",
        )

    target_list = [t.strip().lower() for t in targets.split(",") if t.strip()]
    result = await import_tenant_backup(temp_path, tenant.tenant_id, target_list)

    # Clean up temp upload file
    if temp_path.exists():
        temp_path.unlink()

    return result
