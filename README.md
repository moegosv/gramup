# GramUp

📝 Um bot para automatizar uploads de vídeos no Telegram.

## 🚀 Funcionalidades
- Upload automático de vídeos de uma pasta local
- Suporte a configuração via arquivo `.env`
- Multiplataforma (Windows/Linux)

## 📋 Pré-requisitos

Certifique-se de ter o seguinte instalado:

- [Python 3.x](https://www.python.org/downloads/) (versão 3.8 ou superior recomendada)
- [FFmpeg](https://ffmpeg.org/download.html) (necessário para processamento de mídia)

## 🔧 Instalação

Siga os passos abaixo para configurar o projeto:

### 1. Instale o FFmpeg e Python

**Para Arch Linux:**
```bash
sudo pacman -S ffmpeg python
Para outros sistemas operacionais:

Baixe o FFmpeg em ffmpeg.org/download.html
Adicione o FFmpeg ao PATH do sistema
Instale o Python em python.org/downloads/

2. Clone o repositório
bashCopygit clone https://github.com/moegosv/gramup
cd gramup
3. Configure o arquivo .env
Crie um arquivo chamado .env e adicione o seguinte conteúdo:
CopyAPI_ID=123456
API_HASH=1a2b3c4d5e6f7890abcdef1234567890
PHONE_NUMBER=+55987654321
SESSION_NAME=bot_session
VIDEO_FOLDER=/home/user/Videos  # Linux
# VIDEO_FOLDER=C:\\Users\\User\\Videos  # Windows (descomente se for usar no Windows)
4. Crie um ambiente virtual
No Windows:
bashCopypython -m venv venv
venv\Scripts\activate
No Linux/Mac:
bashCopypython3 -m venv venv
source venv/bin/activate
5. Instale as dependências
bashCopypip install -r requirements.txt
6. Inicie o projeto
bashCopypython main.py
Copy
Isso deve fornecer um README bem organizado para seu projeto GramUp no GitHub. A estrutura está mais clara e as instruções estão organizadas em passos numerados para facilitar o entendimento e a configuração.RetryClaude does not have the ability to run the code it generates yet. Claude does not have internet access. Links provided may not be accurate or up to date.Claude can make mistakes. Please double-check responses.
