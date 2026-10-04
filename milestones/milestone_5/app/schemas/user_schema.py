"""checks for register and login.bad format comes back as 422."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.permissions import ROLES


class UserCreate(BaseModel):
    # role is not a field.sending one is 422,not a silent customer.
    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=100)
    email: EmailStr
    password: str
    mobile: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def password_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must meet minimum length of 8 characters")
        return value

    @field_validator("mobile")
    @classmethod
    def mobile_valid(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isdigit() or len(cleaned) != 10:
            raise ValueError("Mobile must be numeric and of valid length (10 digits)")
        return cleaned


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    # password is not sent back in any response.
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: str
    mobile: str
    role: str


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str

    @field_validator("role")
    @classmethod
    def role_known(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in ROLES:
            raise ValueError("Role must be CUSTOMER, ADMIN, or SUPPORT")
        return cleaned


class RegisterResponse(BaseModel):
    message: str
    user: UserResponse


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
