import asyncio
from typing import Any, List, Optional

from aiogram import Bot, Dispatcher, Router
from pydantic import BaseModel, ConfigDict, Field, field_validator

from conversator.router_generator import generate_router


class ClientBase(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=50)
    table_id: str = Field(..., min_length=5, pattern=r'^[a-zA-Z0-9_-]+$')
    sheet_id: str = Field(...)
    price_id: Optional[str] = Field(
        default=None)
    price_sheet: Optional[str] = Field(
        default=None)
    channel_id: str = Field(..., description="ID канала (-1001234567890) или юзернейм (@channel_name)",
                            pattern=r'^(?:-100\d+|@[a-zA-Z0-9_]{5,32})$')
    manager_ids: List[int] = Field(..., min_items=0)
    token: str = Field(..., pattern=r'^\d{9,10}:[a-zA-Z0-9_-]{35}$')


class ClientCreateRequest(ClientBase):
    pass


class ClientData(ClientBase):
    """Модель данных клиента (с автогенерируемыми полями)"""
    # Автогенерируемые поля
    router: Optional[Router] = Field(default=None, exclude=True)
    bot: Optional[Bot] = Field(default=None, exclude=True)
    dp: Optional[Dispatcher] = Field(default=None, exclude=True)
    task: Optional[asyncio.Task] = Field(default=None, exclude=True)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra='ignore',
        validate_default=True
    )
    
    @field_validator('price_id', 'price_sheet', mode='before')
    def empty_str_to_none(cls, v):
        if v == 0:
            return None
        return v

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.router is None:
            self.router = generate_router(self)

