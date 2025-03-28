from celery import Celery
from app.services.encryption_service import encode_text, decode_text

celery_app = Celery("worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json'
)

@celery_app.task
def encode_task(text: str, key: str):
    return encode_text(text, key)

@celery_app.task
def decode_task(encoded_data: str, key: str, huffman_codes: dict, padding: int):
    return decode_text(encoded_data, key, huffman_codes, padding)
