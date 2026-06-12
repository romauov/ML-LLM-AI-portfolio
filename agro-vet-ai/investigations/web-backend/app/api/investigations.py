"""API endpoints for investigation management."""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from app.services.investigation_manager import InvestigationManager
from app.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/investigations", tags=["investigations"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateInvestigationRequest(BaseModel):
    """Request to create a new investigation."""
    farm_name: str = Field(..., description="Name of the farm")
    problem_type: str = Field(..., description="Type of problem (e.g., neonatal_diarrhea, respiratory)")
    description: Optional[str] = Field(None, description="Initial incident description")


class InvestigationInfo(BaseModel):
    """Information about an investigation."""
    investigation_id: str
    path: str
    created: Optional[str] = None
    status: Optional[str] = None
    files: List[str] = []


class InvestigationFile(BaseModel):
    """Single investigation file content."""
    file_name: str
    content: str
    exists: bool


class UpdateFileRequest(BaseModel):
    """Request to update a file in investigation."""
    file_name: str = Field(..., description="File name (e.g., 00_incident.md)")
    content: str = Field(..., description="New file content")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/create", response_model=InvestigationInfo)
async def create_investigation(
    req: CreateInvestigationRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    Create a new investigation directory with initial files.

    Returns investigation ID and path.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # Create investigation using async method
        investigation = await investigation_manager.create_investigation(
            farm_name=req.farm_name,
            animal_type="pig",  # Default animal type
            problem_type=req.problem_type,
            description=req.description or "Initial investigation"
        )

        # List files using async method
        files = await investigation_manager.list_files(investigation.id)

        return InvestigationInfo(
            investigation_id=investigation.id,
            path=investigation.path,
            created=investigation.created_at.isoformat(),
            status=investigation.status.value,
            files=files,
        )

    except Exception as e:
        logger.error(f"Failed to create investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[InvestigationInfo])
async def list_investigations(http_request: Request, api_key: str = Depends(verify_api_key)):
    """
    List all investigations in the workspace.

    Returns list of investigation IDs with metadata.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # Use async method to list investigations
        investigations_list = await investigation_manager.list_investigations()

        investigations = []
        for inv_item in investigations_list:
            # Get detailed info for each investigation
            inv_detail = await investigation_manager.get_investigation(inv_item.id)

            # List files using async method
            files = await investigation_manager.list_files(inv_item.id)

            investigations.append(InvestigationInfo(
                investigation_id=inv_item.id,
                path=inv_detail.path,
                created=inv_detail.created_at.isoformat(),
                status=inv_detail.status.value,
                files=files,
            ))

        return investigations

    except Exception as e:
        logger.error(f"Failed to list investigations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investigation_id}", response_model=InvestigationInfo)
async def get_investigation(investigation_id: str, http_request: Request, api_key: str = Depends(verify_api_key)):
    """
    Get information about a specific investigation.

    Returns investigation metadata and file list.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # Get investigation details using async method
        investigation = await investigation_manager.get_investigation(investigation_id)

        # List files using async method
        files = await investigation_manager.list_files(investigation_id)

        return InvestigationInfo(
            investigation_id=investigation.id,
            path=investigation.path,
            created=investigation.created_at.isoformat(),
            status=investigation.status.value,
            files=files,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investigation_id}/files/{file_name}", response_model=InvestigationFile)
async def get_file(investigation_id: str, file_name: str, http_request: Request, api_key: str = Depends(verify_api_key)):
    """
    Get content of a specific file in investigation.

    Returns file content or error if not found.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # Read file using async method
        content = await investigation_manager.read_file(investigation_id, file_name)

        return InvestigationFile(
            file_name=file_name,
            content=content,
            exists=True,
        )

    except FileNotFoundError:
        return InvestigationFile(
            file_name=file_name,
            content="",
            exists=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{investigation_id}/files")
async def update_file(
    investigation_id: str,
    req: UpdateFileRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    Update or create a file in investigation.

    Writes content to specified file.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # Write file using async method
        await investigation_manager.write_file(
            investigation_id=investigation_id,
            filename=req.file_name,
            content=req.content
        )

        return {
            "status": "ok",
            "message": f"File {req.file_name} updated successfully",
            "file_path": str(investigation_manager.investigations_path / investigation_id / req.file_name),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investigation_id}/files", response_model=InvestigationInfo)
async def list_investigation_files(investigation_id: str, http_request: Request, api_key: str = Depends(verify_api_key)):
    """
    Get list of files in a specific investigation.

    Returns list of filenames in the investigation.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # List files using async method
        files = await investigation_manager.list_files(investigation_id)

        # Get investigation details for path
        investigation = await investigation_manager.get_investigation(investigation_id)

        return InvestigationInfo(
            investigation_id=investigation_id,
            path=investigation.path,
            files=files,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files in investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{investigation_id}")
async def delete_investigation(investigation_id: str, http_request: Request, api_key: str = Depends(verify_api_key)):
    """
    Delete an investigation (move to trash or remove entirely).

    WARNING: This is a destructive operation.
    """
    try:
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager
        inv_path = investigation_manager.investigations_path / investigation_id

        # Check if investigation exists using async method
        if not await asyncio.to_thread(lambda: inv_path.exists()):
            raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")

        # TODO: Implement safe deletion (move to .trash folder instead of removing)
        # For now, just rename to .deleted_{investigation_id}
        deleted_path = investigation_manager.investigations_path / f".deleted_{investigation_id}"

        await asyncio.to_thread(lambda: inv_path.rename(deleted_path))

        return {
            "status": "ok",
            "message": f"Investigation {investigation_id} deleted (moved to {deleted_path.name})",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
