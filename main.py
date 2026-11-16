"""Terminal da NOW AI; preserva a experiência da versão 0.1."""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name('.env'))
from now_engine.core import route

def main():
    print('🎮 NOW AI 0.2 | Digite ajuda para comandos; sair para encerrar.')
    while True:
        try:
            message = input('\nVocê: ').strip()
        except (KeyboardInterrupt, EOFError):
            break
        if message.lower() in {'sair', 'exit'}:
            break
        if message:
            response = route(message)
            print(f"NOW [{response['provider']}]: {response['reply']}")
    print('NOW: Até a próxima partida!')

if __name__ == '__main__':
    main()
