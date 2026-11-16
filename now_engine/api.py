"""API local da NOW; não expor publicamente sem autenticação e HTTPS."""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .core import route

app = FastAPI(title='NOW Engine', version='0.2.0', docs_url='/docs')

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

@app.get('/health')
def health():
    return {'status': 'ok', 'engine': 'NOW AI', 'version': '0.2.0'}

@app.post('/v1/chat')
def chat(payload: ChatRequest):
    return route(payload.message)
