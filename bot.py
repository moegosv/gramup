import asyncio
import os
import curses
import logging
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeVideo, Channel
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from FastTelethon import upload_file
import ffmpeg
import tempfile
from PIL import Image
import io
from colorama import init, Fore, Back, Style
from dotenv import load_dotenv

load_dotenv()
init()
logging.basicConfig(level=logging.ERROR)

# Configurações
CONFIG_FILE = "config.txt"
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SESSION_NAME = os.getenv("SESSION_NAME", "bot_session")
VIDEO_FOLDER = os.getenv("VIDEO_FOLDER", "/")

def load_config():
    """Carrega a configuração salva do arquivo"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:  # Corrigido: removido "Ascending"
                return lines[0].strip(), lines[1].strip()
    return None, None

def save_config(destination, chat_id=None):
    """Salva a configuração no arquivo"""
    with open(CONFIG_FILE, 'w') as f:
        f.write(f"{destination}\n")
        if chat_id:
            f.write(f"{chat_id}\n")

async def list_chats(client):
    """Lista todos os chats, canais e grupos disponíveis"""
    result = await client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))

    chats = []
    for dialog in result.chats:
        if isinstance(dialog, Channel):
            chats.append({
                'id': dialog.id,
                'title': dialog.title,
                'type': 'channel' if dialog.broadcast else 'group'
            })
    return chats

def select_chat_interactively(chats):
    """Menu interativo para seleção de chat"""
    def draw_menu(stdscr):
        stdscr.clear()
        curses.curs_set(0)  # Esconde o cursor
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Cabeçalho
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # Texto normal
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Item selecionado

        selected = 0
        max_y, max_x = stdscr.getmaxyx()

        while True:
            stdscr.clear()
            header = "Selecione o Canal/Grupo"
            stdscr.addstr(0, 0, " " * max_x, curses.color_pair(1))
            stdscr.addstr(0, (max_x - len(header)) // 2, header, curses.color_pair(1))

            visible_rows = max_y - 4
            start_idx = max(0, min(selected - visible_rows // 2, len(chats) - visible_rows))

            for i in range(min(visible_rows, len(chats))):
                idx = i + start_idx
                if idx < len(chats):
                    chat = chats[idx]
                    if idx == selected:
                        color_pair = curses.color_pair(3)
                    else:
                        color_pair = curses.color_pair(2)

                    chat_type = "Canal" if chat['type'] == 'channel' else "Grupo"
                    line = f"{idx+1:3}. [{chat_type}] {chat['title']} (ID: -100{chat['id']})"
                    stdscr.addstr(i + 2, 0, line[:max_x-1], color_pair)

            if len(chats) > visible_rows:
                if start_idx > 0:
                    stdscr.addstr(1, max_x - 10, "↑ Mais ↑", curses.color_pair(2))
                if start_idx + visible_rows < len(chats):
                    stdscr.addstr(max_y - 1, max_x - 10, "↓ Mais ↓", curses.color_pair(2))

            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(chats) - 1:
                selected += 1
            elif key == ord('\n'):
                return chats[selected]
            elif key == 27:  # ESC
                return None

    return curses.wrapper(draw_menu)

async def get_destination(client):
    """Obtém o destino dos uploads com opção interativa"""
    last_dest, last_chat = load_config()

    if last_dest:
        print(f"\n{Fore.CYAN}Último destino configurado: {Fore.YELLOW}{last_dest}{Style.RESET_ALL}")
        if last_dest == "channel" and last_chat:
            try:
                entity = await client.get_entity(int(last_chat))
                print(f"{Fore.CYAN}Último chat usado: {Fore.YELLOW}{entity.title} (ID: {last_chat}){Style.RESET_ALL}")
            except:
                print(f"{Fore.CYAN}Último chat usado: {Fore.YELLOW}{last_chat}{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}┌{'─' * 33}┐{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│ Escolha uma opção:                │{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│ {Fore.WHITE}1 - Usar o mesmo destino            {Style.RESET_ALL} {Fore.GREEN}│{Style.RESET_ALL}")
        print(f"{Fore.GREEN}│ {Fore.WHITE}2 - Configurar novo destino         {Style.RESET_ALL} {Fore.GREEN}│{Style.RESET_ALL}")
        print(f"{Fore.GREEN}└{'─' * 33}┘{Style.RESET_ALL}")

        choice = input(f"\n{Fore.YELLOW}Opção (1/2): {Style.RESET_ALL}")
        if choice == '1':
            if last_dest == "channel" and last_chat and not last_chat.startswith('-100'):
                last_chat = f"-100{last_chat}"
            return last_dest, last_chat

    print(f"\n{Fore.GREEN}┌{'─' * 33}┐{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ Onde deseja enviar os vídeos?      │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {Fore.WHITE}1 - Mensagens Salvas                {Style.RESET_ALL} {Fore.GREEN}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {Fore.WHITE}2 - Selecionar Canal/Grupo          {Style.RESET_ALL} {Fore.GREEN}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {Fore.WHITE}3 - Digitar ID manualmente          {Style.RESET_ALL} {Fore.GREEN}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}└{'─' * 33}┘{Style.RESET_ALL}")

    dest_choice = input(f"\n{Fore.YELLOW}Opção (1/2/3): {Style.RESET_ALL}")

    if dest_choice == '1':
        save_config("saved")
        return "saved", None
    elif dest_choice == '2':
        chats = await list_chats(client)
        if not chats:
            print(f"{Fore.RED}Nenhum canal/grupo encontrado!{Style.RESET_ALL}")
            return "saved", None

        selected_chat = select_chat_interactively(chats)
        if selected_chat:
            full_chat_id = f"-100{selected_chat['id']}"
            save_config("channel", full_chat_id)
            return "channel", full_chat_id
        else:
            print(f"{Fore.RED}Nenhum chat selecionado, usando Mensagens Salvas.{Style.RESET_ALL}")
            return "saved", None
    elif dest_choice == '3':
        chat_id = input(f"\n{Fore.CYAN}Digite o ID do canal/grupo (com ou sem -100): {Style.RESET_ALL}")
        if chat_id.startswith('-100'):
            full_chat_id = chat_id
        else:
            full_chat_id = f"-100{chat_id}" if not chat_id.startswith('-') else chat_id
        save_config("channel", full_chat_id)
        return "channel", full_chat_id
    else:
        print(f"{Fore.RED}Opção inválida, usando Mensagens Salvas por padrão.{Style.RESET_ALL}")
        return "saved", None

def get_file_size(file_path):
    """Obtém o tamanho formatado do arquivo"""
    size_bytes = os.path.getsize(file_path)
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"

def calculate_total_size(file_paths):
    """Calcula o tamanho total dos arquivos"""
    total_bytes = sum(os.path.getsize(path) for path in file_paths)
    if total_bytes < 1024 * 1024:
        return f"{total_bytes / 1024:.1f}KB"
    elif total_bytes < 1024 * 1024 * 1024:
        return f"{total_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{total_bytes / (1024 * 1024 * 1024):.2f}GB"

def get_video_metadata(file_path: str) -> tuple:
    """Obtém metadados do vídeo usando ffmpeg"""
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            raise ValueError("Nenhum stream de vídeo encontrado.")
        duration = float(video_stream['duration'])
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        return duration, width, height
    except Exception as e:
        print(f"Erro ao obter metadados do vídeo {file_path}: {e}")
        return 0, 1280, 720

def extract_thumbnail(file_path: str) -> bytes:
    """Extrai thumbnail do vídeo"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            duration, _, _ = get_video_metadata(file_path)
            time_pos = min(duration * 0.2, 10)

            (
                ffmpeg
                .input(file_path, ss=time_pos)
                .output(temp_file.name, vframes=1)
                .overwrite_output()
                .run(quiet=True)
            )

            img = Image.open(temp_file.name)
            img.thumbnail((320, 320))

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            return img_byte_arr.getvalue()

    except Exception as e:
        print(f"Erro ao extrair thumbnail do vídeo {file_path}: {e}")
        return None

def clean_filename(filename: str) -> str:
    """Limpa o nome do arquivo para usar como legenda"""
    base = os.path.splitext(filename)[0]
    while '.mp4' in base or '.mkv' in base or '.avi' in base or '.mov' in base:
        base = base.replace('.mp4', '').replace('.mkv', '').replace('.avi', '').replace('.mov', '')
    return base

async def upload_video(client: TelegramClient, file_path: str, file_name: str,
                      destination: str, chat_id: str = None, progress_callback=None):
    """Envia o vídeo para o destino especificado"""
    with open(file_path, 'rb') as file:
        input_file = await upload_file(client, file, file_name, progress_callback=progress_callback)

    duration, width, height = get_video_metadata(file_path)
    thumb = extract_thumbnail(file_path)
    caption = clean_filename(file_name)

    if destination == "saved":
        await client.send_file(
            'me',
            input_file,
            caption=caption,
            thumb=thumb,
            attributes=[DocumentAttributeVideo(
                duration=int(duration),
                w=width,
                h=height,
                supports_streaming=True
            )],
            force_document=False
        )
        print(f"\n{Fore.GREEN}Arquivo enviado para Mensagens Salvas!{Style.RESET_ALL}")
    else:
        try:
            chat_id = int(chat_id) if chat_id.startswith('-100') else int(f"-100{chat_id}")
            await client.send_file(
                chat_id,
                input_file,
                caption=caption,
                thumb=thumb,
                attributes=[DocumentAttributeVideo(
                    duration=int(duration),
                    w=width,
                    h=height,
                    supports_streaming=True
                )],
                force_document=False
            )
            print(f"\n{Fore.GREEN}Arquivo enviado para o canal/grupo!{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}Erro ao enviar para o canal: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Enviando para Mensagens Salvas como fallback...{Style.RESET_ALL}")
            await upload_video(client, file_path, file_name, "saved")

def progress_callback(current: int, total: int):
    """Callback para mostrar progresso do upload"""
    percent = current / total * 100
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f"\r{Fore.CYAN}Progresso: {Fore.YELLOW}[{bar}] {percent:.1f}%{Style.RESET_ALL}", end='')

def get_video_files(folder: str) -> list:
    """Lista arquivos de vídeo na pasta"""
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov')
    files = [f for f in os.listdir(folder) if f.lower().endswith(video_extensions)]
    files.sort()
    return files

def display_video_list(videos, folder):
    """Exibe lista de vídeos encontrados"""
    print(f"\n{Fore.CYAN}Vídeos encontrados:{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")

    total_size_bytes = 0
    for i, video in enumerate(videos):
        file_path = os.path.join(folder, video)
        size_bytes = os.path.getsize(file_path)
        total_size_bytes += size_bytes
        size_str = get_file_size(file_path)
        bg_color = Back.BLACK if i % 2 == 0 else ""
        print(f"{bg_color}{Fore.GREEN}{i+1:2}. {Fore.WHITE}{video} {Fore.YELLOW}({size_str}){Style.RESET_ALL}")

    if total_size_bytes < 1024 * 1024:
        total_size = f"{total_size_bytes / 1024:.1f}KB"
    elif total_size_bytes < 1024 * 1024 * 1024:
        total_size = f"{total_size_bytes / (1024 * 1024):.1f}MB"
    else:
        total_size = f"{total_size_bytes / (1024 * 1024 * 1024):.2f}GB"

    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total: {Fore.WHITE}{len(videos)} arquivos {Fore.YELLOW}({total_size}){Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'─' * 60}{Style.RESET_ALL}")

def curses_menu(stdscr, video_files: list, folder: str):
    """Menu interativo para seleção de vídeos"""
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)

    selected = 0
    to_upload = set()
    file_sizes = {}
    for video in video_files:
        file_path = os.path.join(folder, video)
        file_sizes[video] = get_file_size(file_path)

    max_y, max_x = stdscr.getmaxyx()

    while True:
        stdscr.clear()
        header = "Telegram Video Uploader"
        stdscr.addstr(0, 0, " " * max_x, curses.color_pair(1))
        stdscr.addstr(0, (max_x - len(header)) // 2, header, curses.color_pair(1))

        stdscr.addstr(2, 0, "Selecione os vídeos para upload (Espaço para marcar, Enter para confirmar):", curses.color_pair(2))
        stdscr.addstr(3, 0, "Pressione 'a' para selecionar todos os vídeos", curses.color_pair(4))

        total_selected_size = 0
        selected_paths = [os.path.join(folder, video_files[i]) for i in to_upload]
        if selected_paths:
            total_selected_size = sum(os.path.getsize(path) for path in selected_paths)

        if total_selected_size > 0:
            if total_selected_size < 1024 * 1024:
                total_size_str = f"{total_selected_size / 1024:.1f}KB"
            elif total_selected_size < 1024 * 1024 * 1024:
                total_size_str = f"{total_selected_size / (1024 * 1024):.1f}MB"
            else:
                total_size_str = f"{total_selected_size / (1024 * 1024 * 1024):.2f}GB"

            stdscr.addstr(5, 0, f"Selecionados: {len(to_upload)} arquivos ({total_size_str})", curses.color_pair(4))
        else:
            stdscr.addstr(5, 0, "Nenhum arquivo selecionado", curses.color_pair(4))

        visible_rows = max_y - 8
        start_idx = max(0, min(selected - visible_rows // 2, len(video_files) - visible_rows))

        for i in range(min(visible_rows, len(video_files))):
            idx = i + start_idx
            if idx < len(video_files):
                video = video_files[idx]
                size_str = file_sizes[video]
                clean_name = clean_filename(video)

                if idx in to_upload:
                    prefix = "[x]"
                    color_pair = curses.color_pair(5)
                else:
                    prefix = "[ ]"
                    color_pair = curses.color_pair(2)

                if idx == selected:
                    color_pair = curses.color_pair(3)

                max_name_length = max_x - 35
                video_name = video if len(video) <= max_name_length else video[:max_name_length-3] + "..."

                line = f"{idx+1:3}. {prefix} {video_name} ({size_str})"
                stdscr.addstr(i + 7, 0, line, color_pair)

                caption_line = f"    └─ {clean_name}"
                if len(caption_line) > max_x:
                    caption_line = caption_line[:max_x-3] + "..."
                stdscr.addstr(i + 7 + 1, 0, caption_line, color_pair)

        if len(video_files) > visible_rows:
            if start_idx > 0:
                stdscr.addstr(6, max_x - 10, "↑ Mais ↑", curses.color_pair(4))
            if start_idx + visible_rows < len(video_files):
                stdscr.addstr(max_y - 1, max_x - 10, "↓ Mais ↓", curses.color_pair(4))

        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(video_files) - 1:
            selected += 1
        elif key == ord(' '):
            if selected in to_upload:
                to_upload.remove(selected)
            else:
                to_upload.add(selected)
        elif key == ord('a'):
            if len(to_upload) == len(video_files):
                to_upload.clear()
            else:
                to_upload = set(range(len(video_files)))
        elif key == ord('\n'):
            return [video_files[i] for i in to_upload]

async def main():
    telethon_logger = logging.getLogger('telethon')
    telethon_logger.setLevel(logging.ERROR)

    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{Fore.CYAN}┌{'─' * 53}┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.BRIGHT}{Fore.WHITE}          Telegram Video Uploader          {Style.RESET_ALL}{Fore.CYAN}│{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└{'─' * 53}┘{Style.RESET_ALL}")

    if not API_ID or not API_HASH:
        print(f"\n{Fore.RED}Erro: Variáveis de ambiente necessárias não configuradas!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Certifique-se de que seu arquivo .env contém:")
        print(f"API_ID=seu_api_id")
        print(f"API_HASH=seu_api_hash{Style.RESET_ALL}")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            if not PHONE_NUMBER:
                print(f"\n{Fore.RED}Erro: Número de telefone não configurado para primeiro login!{Style.RESET_ALL}")
                return

            print(f"\n{Fore.GREEN}Conectando como: {Style.BRIGHT}{PHONE_NUMBER}{Style.RESET_ALL}")
            await client.start(phone=PHONE_NUMBER)
            print(f"\n{Fore.GREEN}✅ Login realizado com sucesso!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✅ Sessão existente conectada com sucesso!{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Erro ao conectar: {e}{Style.RESET_ALL}")
        return

    if not os.path.exists(VIDEO_FOLDER):
        print(f"\n{Fore.RED}A pasta {VIDEO_FOLDER} não existe!{Style.RESET_ALL}")
        await client.disconnect()
        return

    video_files = get_video_files(VIDEO_FOLDER)
    if not video_files:
        print(f"\n{Fore.RED}Nenhum vídeo encontrado na pasta!{Style.RESET_ALL}")
        await client.disconnect()
        return

    print(f"\n{Fore.CYAN}Total de {Style.BRIGHT}{len(video_files)}{Style.RESET_ALL}{Fore.CYAN} vídeos encontrados na pasta.{Style.RESET_ALL}")

    destination, chat_id = await get_destination(client)

    print(f"\n{Fore.GREEN}┌{'─' * 33}┐{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ Escolha uma opção:                │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {Fore.WHITE}1 - Selecionar vídeos individualmente{Style.RESET_ALL} {Fore.GREEN}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {Fore.WHITE}2 - Enviar todos os vídeos da pasta{Style.RESET_ALL}  {Fore.GREEN}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}└{'─' * 33}┘{Style.RESET_ALL}")

    choice = input(f"\n{Fore.YELLOW}Opção (1/2): {Style.RESET_ALL}")

    selected_videos = []
    if choice == '1':
        os.system('cls' if os.name == 'nt' else 'clear')
        selected_videos = curses.wrapper(curses_menu, video_files, VIDEO_FOLDER)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}┌{'─' * 53}┐{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│{Style.BRIGHT}{Fore.WHITE}          Telegram Video Uploader          {Style.RESET_ALL}{Fore.CYAN}│{Style.RESET_ALL}")
        print(f"{Fore.CYAN}└{'─' * 53}┘{Style.RESET_ALL}")
    elif choice == '2':
        selected_videos = video_files
        display_video_list(video_files, VIDEO_FOLDER)
    else:
        print(f"\n{Fore.RED}Opção inválida!{Style.RESET_ALL}")
        await client.disconnect()
        return

    if not selected_videos:
        print(f"\n{Fore.YELLOW}Nenhum vídeo selecionado para upload.{Style.RESET_ALL}")
        await client.disconnect()
        return

    selected_paths = [os.path.join(VIDEO_FOLDER, video) for video in selected_videos]
    total_size = calculate_total_size(selected_paths)

    print(f"\n{Fore.YELLOW}┏{'━' * 50}┓{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}┃ {Style.BRIGHT}Vídeos selecionados: {len(selected_videos)} ({total_size}){Style.RESET_ALL}{Fore.YELLOW} {' ' * (24 - len(str(len(selected_videos))) - len(total_size))}┃{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}┗{'━' * 50}┛{Style.RESET_ALL}")

    for i, video in enumerate(selected_videos):
        file_path = os.path.join(VIDEO_FOLDER, video)
        size = get_file_size(file_path)
        clean_name = clean_filename(video)

        bg_color = "" if i % 2 == 0 else Back.BLACK

        print(f"\n{bg_color}{Fore.GREEN}{i+1}. {Fore.WHITE}{video} {Fore.YELLOW}({size}){Style.RESET_ALL}")
        print(f"{bg_color}{Fore.CYAN}   └─ {clean_name}{Style.RESET_ALL}")

    dest_name = "Mensagens Salvas" if destination == "saved" else f"o canal/grupo (ID: {chat_id})"
    print(f"\n{Fore.MAGENTA}Deseja enviar esses vídeos para {dest_name}? (s/n): {Style.RESET_ALL}", end="")
    confirmation = input()

    if confirmation.lower() != 's':
        print(f"\n{Fore.RED}Upload cancelado.{Style.RESET_ALL}")
        await client.disconnect()
        return

    for video in selected_videos:
        file_path = os.path.join(VIDEO_FOLDER, video)
        print(f"\n{Fore.CYAN}Iniciando upload de {Style.BRIGHT}{video}{Style.RESET_ALL}")
        await upload_video(client, file_path, video, destination, chat_id, progress_callback)

    print(f"\n{Fore.GREEN}{Style.BRIGHT}Todos os uploads concluídos!{Style.RESET_ALL}")
    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Programa interrompido pelo usuário.{Style.RESET_ALL}")

