import yt_dlp
import os
import subprocess
import sys
import shutil
import re
import time
import random

# --- 🔧 ФІКС КОДУВАННЯ (для Termux/Windows) ---
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# ⚙️ ВАШІ ПРОКСІ (Вже налаштовані)
# ==========================================
PROXY_LIST = [
    "http://uallevim:wo1dty2gejpb@142.111.48.253:7030",
    "http://uallevim:wo1dty2gejpb@23.95.150.145:6114",
    "http://uallevim:wo1dty2gejpb@198.23.239.134:6540",
    "http://uallevim:wo1dty2gejpb@107.172.163.27:6543",
    "http://uallevim:wo1dty2gejpb@198.105.121.200:6462",
    "http://uallevim:wo1dty2gejpb@64.137.96.74:6641",
    "http://uallevim:wo1dty2gejpb@84.247.60.125:6095",
    "http://uallevim:wo1dty2gejpb@216.10.27.159:6837",
    "http://uallevim:wo1dty2gejpb@23.26.71.145:5628",
    "http://uallevim:wo1dty2gejpb@23.27.208.120:5830",
]

# --- ШЛЯХИ ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "Downloads")
MUSIC_DIR = os.path.join(DOWNLOAD_DIR, "Music")
VIDEO_DIR = os.path.join(DOWNLOAD_DIR, "Video")


# --- ФУНКЦІЇ ---

def get_random_proxy():
    """Повертає випадковий проксі або None"""
    if PROXY_LIST:
        return random.choice(PROXY_LIST)
    return None


def get_cookies_path():
    """Шукає cookies.txt поруч зі скриптом"""
    path = os.path.join(SCRIPT_DIR, "cookies.txt")
    if os.path.exists(path): return path
    return None


def ensure_folders():
    if not os.path.exists(MUSIC_DIR): os.makedirs(MUSIC_DIR)
    if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)


def clean_spotify_url(dirty_url):
    """Магічна функція: перетворює брудні посилання на чисті"""
    # 1. Якщо це вже чисте посилання
    if "open.spotify.com" in dirty_url and "track" in dirty_url:
        return dirty_url

    # 2. Витягуємо ID через Regex (працює з googleusercontent та іншим сміттям)
    match = re.search(r'(track|playlist|album|artist)[/:]([a-zA-Z0-9]{22})', dirty_url)
    if match:
        Type = match.group(1)
        ID = match.group(2)
        # Формуємо ідеально чисте посилання
        return f"https://open.spotify.com/{Type}/{ID}"

    return None


def download_spotify(query):
    ensure_folders()

    # 1. Очищення посилання
    clean_url = clean_spotify_url(query)

    if clean_url:
        print(f"✅ Посилання очищено: {clean_url}")
        target = clean_url
    else:
        # Якщо це просто назва пісні
        print(f"🔍 Пошук за назвою: {query}")
        target = query

    # 2. Підготовка команди
    output_tmpl = os.path.join(MUSIC_DIR, "{artist} - {title}.{output-ext}")

    # Використовуємо subprocess для виклику spotdl
    command = ["spotdl", target, "--output", output_tmpl, "--overwrite", "skip"]

    # Додаємо проксі
    proxy = get_random_proxy()
    if proxy:
        command.extend(["--proxy", proxy])
        print(f"🕵️ Proxy активовано")

    if get_cookies_path():
        command.extend(["--cookie-file", get_cookies_path()])

    # 3. Виконання
    try:
        print("⏳ Завантаження...")
        subprocess.run(command)
        print("\n✨ Завдання завершено.")
    except Exception as e:
        print(f"❌ Помилка: {e}")


def download_youtube(url):
    ensure_folders()
    print("\n--- 🔴 YouTube ---")
    print("1. 🎵 MP3 (Музика)")
    print("2. 🎬 MP4 (Відео)")
    choice = input(">> ").strip()

    if choice == '2':
        save_path = VIDEO_DIR
        fmt = 'bestvideo+bestaudio/best'
    else:
        save_path = MUSIC_DIR
        fmt = 'bestaudio/best'

    # Налаштування
    ydl_opts = {
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'format': fmt,
        'noplaylist': True,
        'quiet': False,
    }

    # Конвертація в MP3
    if choice != '2':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    # Проксі для YouTube
    proxy = get_random_proxy()
    if proxy:
        ydl_opts['proxy'] = proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ Збережено в: {save_path}")
    except Exception as e:
        print(f"❌ Помилка YouTube: {e}")


def main():
    # Перевірка spotdl
    if not shutil.which("spotdl"):
        print("⚠️ Увага: spotdl не встановлено. Встановлюю...")
        subprocess.run([sys.executable, "-m", "pip", "install", "spotdl", "-U"])

    while True:
        print("\n" + "=" * 30)
        print("музика")
        print("=" * 30)
        print("1. 🟢 Spotify (Auto-fix посилань)")
        print("2. 🔴 YouTube (MP3/MP4)")
        print("q. Вихід")

        choice = input(">> ").strip()

        if choice.lower() in ['q', 'exit']:
            break

        if choice == '1':
            q = input("Вставте посилання або назву: ").strip()
            if q: download_spotify(q)

        elif choice == '2':
            url = input("Вставте посилання YouTube: ").strip()
            if url: download_youtube(url)

        # Якщо користувач просто вставив посилання в головне меню
        elif "spotify" in choice or "googleusercontent" in choice:
            download_spotify(choice)
        elif "youtu" in choice:
            download_youtube(choice)
        else:
            # Спроба пошуку
            download_spotify(choice)


if __name__ == "__main__":
    main()