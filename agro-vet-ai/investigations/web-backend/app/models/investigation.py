"""Pydantic models for veterinary investigations."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    """Investigation status enum."""

    ACTIVE = "active"
    COMPLETED = "completed"
    PENDING = "pending"


class InvestigationCreate(BaseModel):
    """Model for creating a new investigation."""

    farm_name: str = Field(..., description="Name of the farm")
    animal_type: str = Field(..., description="Type of animals (e.g., pigs, poultry)")
    problem_type: str = Field(..., description="Type of problem (e.g., diarrhea, respiratory)")
    description: str = Field(..., description="Initial description of the incident")


class Investigation(BaseModel):
    """Investigation model."""

    id: str = Field(..., description="Investigation ID (YYYY-MM-DD_farm-name)")
    farm_name: str = Field(..., description="Name of the farm")
    animal_type: str = Field(..., description="Type of animals")
    problem_type: str = Field(..., description="Type of problem")
    status: InvestigationStatus = Field(
        default=InvestigationStatus.ACTIVE, description="Current status"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    path: str = Field(..., description="Absolute path to investigation directory")


class InvestigationFile(BaseModel):
    """Investigation file model."""

    filename: str = Field(..., description="File name")
    content: str = Field(..., description="File content")
    size: int = Field(..., description="File size in bytes")
    modified_at: Optional[datetime] = Field(None, description="Last modification timestamp")


class InvestigationListItem(BaseModel):
    """Lightweight investigation model for listing."""

    id: str = Field(..., description="Investigation ID")
    farm_name: str = Field(..., description="Name of the farm")
    status: InvestigationStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
