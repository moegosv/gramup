# Antes de começar

Certifique-se de ter o seguinte instalado:

- [Python 3.x](https://www.python.org/downloads/) (versão 3.8 ou superior recomendada)
- [FFmpeg](https://ffmpeg.org/download.html) (necessário para processamento de mídia)

# Instalação

Siga os passos abaixo para configurar o projeto:

## 1. Instale o FFmpeg e Python

- **Para Arch Linux:**
  ```bash
  sudo pacman -S ffmpeg python
  
  Outros sistemas operacionais:
        Baixe o FFmpeg em ffmpeg.org/download.html e siga as instruções para seu sistema.
        Adicione o FFmpeg ao PATH do sistema para usá-lo pelo terminal.
        Instale o Python em python.org/downloads/, se necessário.

2. Clone o repositório
bash
git clone https://github.com/moegosv/gramup
cd gramup
3. Configure o arquivo .env

Crie um arquivo chamado .env e adicione o seguinte conteúdo:
plaintext
API_ID=123456
API_HASH=1a2b3c4d5e6f7890abcdef1234567890
PHONE_NUMBER=+55987654321
SESSION_NAME=bot_session
VIDEO_FOLDER=/home/user/Videos  # Linux
# VIDEO_FOLDER=C:\\Users\\User\\Videos  # Windows (descomente se for usar no Windows)
4. Crie um ambiente virtual

    No Windows:
    bash

python -m venv venv
venv\Scripts\activate
No Linux/Mac:
bash

    python3 -m venv venv
    source venv/bin/activate

5. Instale as dependências
bash
pip install -r requirements.txt
6. Inicie o projeto
bash
python main.py
```
