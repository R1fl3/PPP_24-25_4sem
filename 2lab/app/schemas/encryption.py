
from pydantic import BaseModel
from typing import Dict

class EncodeRequest(BaseModel):
    text: str
    key: str

class EncodeResponse(BaseModel):
    encoded_data: str
    key: str
    huffman_codes: Dict[str, str]
    padding: int

class DecodeRequest(BaseModel):
    encoded_data: str
    key: str
    huffman_codes: Dict[str, str]
    padding: int

class DecodeResponse(BaseModel):
    decoded_text: str
