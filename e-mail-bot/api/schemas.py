"""
объекты запроса и ответа

@author Sergei Romanov
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional

class UserRequest(BaseModel):
    site: str
    user_id: int
    system_id: int
    reglament_id: Optional[str] = None
    messages: List[dict]

class UserResponse(BaseModel):
    quick_reply: str

class GptTemplaterRequest(BaseModel):
    deal_type: Optional[str] = ""
    title: Optional[str] = ""
    descr: Optional[str] = ""
    category_id: Optional[str] = ""
    type1: Optional[str] = ""
    type2: Optional[str] = ""
    state: Optional[str] = ""
    certification: Optional[str] = ""
    price: Optional[int] = 0
    delivery_info: Optional[str] = ""
    unitCount: Optional[str] = ""
    unit: Optional[str] = ""
    user_company_id: Optional[int] = 0
    user_company_name: Optional[str] = ""
    author_firstname: Optional[str] = ""
    author_lastname: Optional[str] = ""
    author_position: Optional[str] = ""
    addresses: Optional[str] = ""
    email: Optional[str] = ""
    phones: Optional[str] = ""
    company_descr: Optional[str] = ""
    model: Optional[str] = None
    temperature: float = 0.9
    
    @field_validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature value, setting to 0.9 if less than 0.9"""
        if v < 0.9:
            return 0.9
        return v

class GptTemplaterResponse(BaseModel):
    title: str
    text: str