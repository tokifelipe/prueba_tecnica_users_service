# utils.py - Funciones puras
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
import re

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración JWT
# En producción se debe usar una clave secreta segura. Además, se recomienda almacenarla en un lugar seguro(secrets) y no "hardcodearla" en el código. Esto lo hago por simplicidad para la prueba tecnica.
SECRET_KEY = "ejemplo_de_clave_secreta_prueba_tecnica"
ALGORITHM = "HS256"


class Phone(BaseModel):
    number: str
    citycode: str
    contrycode: str


class UserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phones: List[Phone]
    
    @validator('email')
    def validate_email_format(cls, v):
        # Valida formato de email específico (aaaaaaa@dominio.cl)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('El formato del correo no es válido')
        return v
    
    @validator('password')
    def validate_password_format(cls, v):
        # Valida formato de contraseña (Una mayúscula, letras minúsculas, y dos números)
        password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d.*\d)[A-Za-z\d]+$'
        if not re.match(password_pattern, v):
            raise ValueError('La contraseña debe contener una mayúscula, letras minúsculas y al menos dos números')
        return v


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phones: Optional[List[Phone]] = None
    
    @validator('email')
    def validate_email_format(cls, v):
        if v is not None:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('El formato del correo no es válido')
        return v
    
    @validator('password')
    def validate_password_format(cls, v):
        if v is not None:
            password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d.*\d)[A-Za-z\d]+$'
            if not re.match(password_pattern, v):
                raise ValueError('La contraseña debe contener una mayúscula, letras minúsculas y al menos dos números')
        return v


def create_access_token(data: dict) -> str:
    """Crear token JWT"""
    to_encode = data.copy()
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def hash_password(password: str) -> str:
    """Hash de la contraseña"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)
