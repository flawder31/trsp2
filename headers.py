from datetime import datetime
from pydantic import BaseModel, Field, validator


class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    @validator('accept_language')
    def validate_accept_language(cls, v):
        if not v:
            raise ValueError('Accept-Language header is required')
        
        parts = v.split(',')
        for part in parts:
            part = part.strip()
            if ';q=' in part:
                lang_part, q_part = part.split(';q=')
                try:
                    q_value = float(q_part)
                    if not (0 <= q_value <= 1):
                        raise ValueError()
                except ValueError:
                    raise ValueError(f'Invalid q-value format in Accept-Language: {q_part}')
        
        return v
    
    class Config:
        populate_by_name = True
        extra = "forbid"


def get_server_time() -> str:
    return datetime.utcnow().isoformat()


class HeadersResponse(BaseModel):
    User_Agent: str
    Accept_Language: str


class InfoResponse(BaseModel):
    message: str
    headers: dict