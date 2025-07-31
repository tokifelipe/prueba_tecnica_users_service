import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pydantic import BaseModel

# Importar funciones y modelos desde utils
from  .utils import (
    create_access_token, 
    hash_password, 
    Phone, 
    UserRequest, 
    UserUpdateRequest
)

app = FastAPI()

# Configuración de logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

# Cliente MongoDB como singleton
mongodb_client = MongoClient("users_service_mongodb", 27017)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phones: List[Phone]
    created: datetime
    modified: datetime
    last_login: datetime
    token: str
    isactive: bool


class MessageResponse(BaseModel):
    mensaje: str


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"mensaje": exc.detail}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"mensaje": str(exc)}
    )


@app.get("/")
async def root():
    logging.info(" User Service (end-point)!")
    return {"mensaje": "API de gestión usuarios funcionando"}


@app.get("/usuarios", response_model=List[UserResponse])
def get_users():
    """
    Obtener todos los usuarios
    """
    logging.info("Obteniendo todos los usuarios")
    try:
        users = []
        for user_doc in mongodb_client.users_service.users.find():
            user_response = UserResponse(
                id=user_doc["id"],
                name=user_doc["name"],
                email=user_doc["email"],
                phones=[Phone(**phone) for phone in user_doc["phones"]],
                created=user_doc["created"],
                modified=user_doc["modified"],
                last_login=user_doc["last_login"],
                token=user_doc["token"],
                isactive=user_doc["isactive"]
            )
            users.append(user_response)
        return users
    except Exception as e:
        logging.error(f"Error al obtener usuarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@app.get("/usuarios/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    """
    Obtener un usuario específico por ID
    """
    logging.info(f"Obteniendo usuario: {user_id}")
    try:
        user_doc = mongodb_client.users_service.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return UserResponse(
            id=user_doc["id"],
            name=user_doc["name"],
            email=user_doc["email"],
            phones=[Phone(**phone) for phone in user_doc["phones"]],
            created=user_doc["created"],
            modified=user_doc["modified"],
            last_login=user_doc["last_login"],
            token=user_doc["token"],
            isactive=user_doc["isactive"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error al obtener usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.patch("/usuarios/{user_id}", response_model=UserResponse)
def partial_update_user(user_id: str, user_update: UserUpdateRequest):
    """
    Actualizar parcialmente un usuario (solo los campos enviados)
    """
    logging.info(f"Actualizando parcialmente usuario: {user_id}")
    try:
        existing_user = mongodb_client.users_service.users.find_one({"id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Prepara documento de actualización solo con campos enviados
        update_doc = {}
        
        if user_update.name is not None:
            update_doc["name"] = user_update.name
            
        if user_update.email is not None:
            # Verifica si el nuevo email ya existe en otro usuario
            if user_update.email != existing_user["email"]:
                email_exists = mongodb_client.users_service.users.find_one({
                    "email": user_update.email,
                    "id": {"$ne": user_id}
                })
                if email_exists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El correo ya registrado"
                    )
            update_doc["email"] = user_update.email
            
        if user_update.password is not None:
            update_doc["password"] = hash_password(user_update.password)
            
        if user_update.phones is not None:
            update_doc["phones"] = [phone.model_dump() for phone in user_update.phones]
        
        # Solo actualizar si hay campos para actualizar
        if update_doc:
            update_doc["modified"] = datetime.now(timezone.utc)
            
            mongodb_client.users_service.users.update_one(
                {"id": user_id},
                {"$set": update_doc}
            )
        
        # Obtener usuario actualizado
        updated_user = mongodb_client.users_service.users.find_one({"id": user_id})
        
        return UserResponse(
            id=updated_user["id"],
            name=updated_user["name"],
            email=updated_user["email"],
            phones=[Phone(**phone) for phone in updated_user["phones"]],
            created=updated_user["created"],
            modified=updated_user["modified"],
            last_login=updated_user["last_login"],
            token=updated_user["token"],
            isactive=updated_user["isactive"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error al actualizar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@app.put("/usuarios/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_request: UserRequest):
    """
    Actualizar un usuario existente
    """
    logging.info(f"Actualizando usuario: {user_id}")
    try:
        existing_user = mongodb_client.users_service.users.find_one({"id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar si el nuevo email ya existe en otro usuario
        if user_request.email != existing_user["email"]:
            email_exists = mongodb_client.users_service.users.find_one({
                "email": user_request.email,
                "id": {"$ne": user_id}
            })
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El correo ya registrado"
                )
        
        now = datetime.now(timezone.utc)
        hashed_password = hash_password(user_request.password)
        
        # Actualizar usuario
        update_doc = {
            "name": user_request.name,
            "email": user_request.email,
            "password": hashed_password,
            "phones": [phone.model_dump() for phone in user_request.phones],
            "modified": now
        }

        mongodb_client.users_service.users.update_one(
            {"id": user_id},
            {"$set": update_doc}
        )
        
        # Obtener usuario actualizado
        updated_user = mongodb_client.users_service.users.find_one({"id": user_id})

        return UserResponse(
            id=updated_user["id"],
            name=updated_user["name"],
            email=updated_user["email"],
            phones=[Phone(**phone) for phone in updated_user["phones"]],
            created=updated_user["created"],
            modified=updated_user["modified"],
            last_login=updated_user["last_login"],
            token=updated_user["token"],
            isactive=updated_user["isactive"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error al actualizar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@app.delete("/usuarios/{user_id}")
def delete_user(user_id: str):
    """
    Eliminar un usuario (soft delete - marcar como inactivo)
    """
    logging.info(f"Eliminando usuario: {user_id}")
    try:
        existing_user = mongodb_client.users_service.users.find_one({"id": user_id})
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Soft delete - marcar como inactivo
        mongodb_client.users_service.users.update_one(
            {"id": user_id},
            {"$set": {"isactive": False, "modified": datetime.now(timezone.utc)}}
        )
        
        return {"mensaje": "Usuario eliminado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error al eliminar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@app.post("/usuarios", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_request: UserRequest):
    """
    Endpoint para crear un nuevo usuario
    """
    logging.info(f"Creando nuevo usuario con email: {user_request.email}")
    
    # Verificar si el correo ya existe
    existing_user = mongodb_client.users_service.users.find_one({"email": user_request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya registrado"
        )
    
    # Crear el nuevo usuario
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Hash de la contraseña
    hashed_password = hash_password(user_request.password)
    
    # Crear token JWT
    token_data = {"user_id": user_id, "email": user_request.email}
    access_token = create_access_token(token_data)
    
    # Preparar documento del usuario
    user_doc = {
        "id": user_id,
        "name": user_request.name,
        "email": user_request.email,
        "password": hashed_password,
        "phones": [phone.model_dump() for phone in user_request.phones],
        "created": now,
        "modified": now,
        "last_login": now,
        "token": access_token,
        "isactive": True
    }
    
    # Insertar en la base de datos
    try:
        mongodb_client.users_service.users.insert_one(user_doc)
        logging.info(f" Nuevo usuario creado: {user_request.name}")
        
        # Preparar respuesta
        response = UserResponse(
            id=user_id,
            name=user_request.name,
            email=user_request.email,
            phones=user_request.phones,
            created=now,
            modified=now,
            last_login=now,
            token=access_token,
            isactive=True
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Error al crear usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
