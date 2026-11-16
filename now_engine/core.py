"""Roteamento: comandos offline -> Ollama local -> Gemini opcional."""
import json
import os
import unicodedata
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SYSTEM = ('Você é a NOW AI, assistente gamer prestativa, bem-humorada e objetiva. '
          'Responda em português brasileiro. Não finja ser humana.')


def offline_command(message: str) -> str | None:
    value = ''.join(c for c in unicodedata.normalize('NFKD', message.strip().lower()) if not unicodedata.combining(c))
    if value in {'oi', 'ola', 'now', 'ei now'}:
        return 'Opa! NOW na área. Qual é a missão?'
    if value in {'ajuda', 'comandos'}:
        return 'Comandos offline: oi, ajuda, horas, data e sair. Perguntas livres usam o modelo local ou Gemini.'
    if value in {'horas', 'que horas sao?', 'que horas sao'}:
        return f'Agora são {datetime.now():%H:%M} no seu computador.'
    if value in {'data', 'que dia e hoje?', 'que dia e hoje'}:
        return f'Hoje é {datetime.now():%d/%m/%Y}.'
    return None


def local_reply(message: str) -> str:
    # Endereço fixo em loopback para impedir chamadas arbitrárias pela API.
    endpoint = 'http://127.0.0.1:11434/api/generate'
    body = json.dumps({'model': os.getenv('OLLAMA_MODEL', 'qwen2.5:0.5b'),
                       'prompt': f'{SYSTEM}\nUsuário: {message}\nNOW:',
                       'stream': False, 'options': {'num_predict': 220}}).encode()
    request = Request(endpoint, data=body, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=90) as response:
        result = json.load(response)
    return result.get('response', '').strip() or 'O modelo local não retornou uma resposta.'


def gemini_reply(message: str) -> str:
    from google import genai
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key or key == 'COLOQUE_SUA_CHAVE_AQUI':
        raise RuntimeError('Gemini não configurado')
    client = genai.Client(api_key=key)
    result = client.models.generate_content(
        model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
        contents=message,
        config={'system_instruction': SYSTEM})
    return result.text or 'Gemini não retornou uma resposta.'


def route(message: str) -> dict:
    answer = offline_command(message)
    if answer is not None:
        return {'reply': answer, 'provider': 'offline'}
    try:
        return {'reply': local_reply(message), 'provider': 'local'}
    except (URLError, HTTPError, TimeoutError, OSError, ValueError, KeyError):
        pass
    if os.getenv('ENABLE_GEMINI_FALLBACK', 'false').lower() == 'true':
        try:
            return {'reply': gemini_reply(message), 'provider': 'gemini'}
        except Exception:
            pass
    return {'reply': 'O modelo local está indisponível. Inicie o Ollama ou habilite o Gemini como alternativa.',
            'provider': 'unavailable'}
