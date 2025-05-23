
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.schemas.encryption import EncodeRequest, EncodeResponse, DecodeRequest, DecodeResponse
from app.services.encryption_service import encode_text, decode_text
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/encode", response_model=EncodeResponse)
def encode_data(request: EncodeRequest, user: str = Depends(get_current_user)):
    return encode_text(request.text, request.key)

@router.post("/decode", response_model=DecodeResponse)
def decode_data(request: DecodeRequest, user: str = Depends(get_current_user)):
    return decode_text(request.encoded_data, request.key, request.huffman_codes, request.padding)
