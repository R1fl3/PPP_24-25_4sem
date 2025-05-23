from celery import Celery
from app.services.encryption_service import encode_text, decode_text

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True
)

@celery_app.task(bind=True)
def encode_task(self, text: str, key: str):
    self.update_state(state='STARTED')
    return encode_text(text, key)

@celery_app.task(bind=True)
def decode_task(self, encoded_data: str, key: str, huffman_codes: dict, padding: int):
    self.update_state(state='STARTED')
    return decode_text(encoded_data, key, huffman_codes, padding)
