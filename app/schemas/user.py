from datetime import datetime
from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: int = Field(..., description="The unique identifier of the user")
    name: str = Field(..., description="The name of the user")
    email: str = Field(..., description="The email address of the user")
    password_hash: str = Field(..., description="The hash of the user's password")
    is_active: bool = Field(default=True, description="Indicates if the user is active")
    created_at: datetime = Field(..., description="The timestamp when the user was created")
