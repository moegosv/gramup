Antes de começar, certifique-se de ter o seguinte instalado:
- [Python 3.x](https://www.python.org/downloads/) (versão 3.8 ou superior recomendada)
- [FFmpeg](https://ffmpeg.org/download.html) (necessário para processamento de mídia)

## Instalação

Siga os passos abaixo para configurar o projeto:

### 1. Instale o FFmpeg e Python
- Para Arch Linux:
sudo pacman -S ffmpeg python

- Outros sistemas operacionais:
- Baixe o FFmpeg em [ffmpeg.org/download.html](https://ffmpeg.org/download.html) e siga as instruções para seu sistema.
- Adicione o FFmpeg ao PATH do sistema para usá-lo pelo terminal.
- Instale o Python em [python.org/downloads/](https://www.python.org/downloads/), se necessário.

Clone o repositório:
git clone https://github.com/moegosv/gramup
cd gramup

Crie uma pasta chamada .env e adicione isso lá:

API_ID=123456
API_HASH=1a2b3c4d5e6f7890abcdef1234567890
PHONE_NUMBER=+55987654321
SESSION_NAME=bot_session
VIDEO_FOLDER=/home/user/Videos # Linux

Crie um ambiente virtual:

- No Windows:
python -m venv venv
venv\Scripts\activate

- No Linux/Mac:
python3 -m venv venv
source venv/bin/activate


- Instale dependências:
pip install -r requirements.txt

Inicie o projeto:
python main.py
