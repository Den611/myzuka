import yt_dlp
import os
import subprocess
import sys
import shutil
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# --- 🔧 ФІКС КОДУВАННЯ (Щоб кирилиця відображалась коректно) ---
sys.stdout.reconfigure(encoding='utf-8')

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

MIN_DELAY = 5  # Мінімум секунд паузи між треками
MAX_DELAY = 15  # Максимум секунд паузи

# --- ШЛЯХИ ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, "Downloads")
MUSIC_DIR = os.path.join(BASE_DIR, "Music")
VIDEO_DIR = os.path.join(BASE_DIR, "Video")

print_lock = Lock()

try:
    from mutagen.easyid3 import EasyID3
except ImportError:
    EasyID3 = None


# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def safe_print(msg):
    with print_lock:
        try:
            print(msg)
        except:
            print(msg.encode('ascii', 'ignore').decode('ascii'))


def get_random_proxy():
    """Повертає випадковий проксі зі списку або None"""
    if PROXY_LIST:
        return random.choice(PROXY_LIST)
    return None


def remove_track_number(file_path):
    if not EasyID3 or not os.path.exists(file_path): return
    if not file_path.endswith(".mp3"): return
    try:
        audio = EasyID3(file_path)
        if 'tracknumber' in audio:
            del audio['tracknumber']
            audio.save()
    except:
        pass


def get_cookies_path():
    cookie_path = os.path.join(SCRIPT_DIR, "cookies.txt")
    if os.path.exists(cookie_path): return cookie_path
    return None


def check_dependencies():
    missing = []
    if not shutil.which("ffmpeg"): missing.append("FFmpeg")
    if not shutil.which("spotdl"): missing.append("spotdl")
    if missing:
        safe_print(f"❌ Не вистачає програм: {', '.join(missing)}")
        safe_print("Будь ласка, встановіть їх або покладіть ffmpeg.exe поруч зі скриптом.")
        return False
    return True


def ensure_folders():
    if not os.path.exists(MUSIC_DIR): os.makedirs(MUSIC_DIR)
    if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)


def clean_filename_for_search(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r"\(.*?\)", "", name)  # Видаляє дужки
    name = re.sub(r"\[.*?\]", "", name)  # Видаляє квадратні дужки
    name = name.replace("_", " ").strip()
    # Видаляє зайві пробіли
    return " ".join(name.split())


# --- ОБРОБКА ФАЙЛІВ (SPOTDL) ---

def process_single_file_task(file, folder_path, trash_path):
    # 1. Затримка перед стартом (щоб потоки не стартували одночасно)
    time.sleep(random.uniform(0.5, 3.0))

    search_query = clean_filename_for_search(file)
    output_format = os.path.join(MUSIC_DIR, "{artist} - {title}.{output-ext}")

    # Підготовка команди
    command = ["spotdl", search_query, "--output", output_format, "--overwrite", "skip", "--max-retries", "3"]

    # Додавання cookies
    if get_cookies_path():
        command.extend(["--cookie-file", get_cookies_path()])

    # Додавання PROXY (Ротація)
    proxy = get_random_proxy()
    if proxy:
        command.extend(["--proxy", proxy])
        # safe_print(f"🕵️ Proxy для {file}: ...{proxy[-4:]}") # Розкоментуйте для дебагу

    try:
        files_before = set(os.listdir(MUSIC_DIR))

        # Виконання команди
        result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='ignore')

        files_after = set(os.listdir(MUSIC_DIR))
        new_files = files_after - files_before

        if new_files:
            new_file_name = list(new_files)[0]
            remove_track_number(os.path.join(MUSIC_DIR, new_file_name))
            shutil.move(os.path.join(folder_path, file), os.path.join(trash_path, file))
            safe_print(f"✅ Оновлено: {file} -> {new_file_name}")

        elif "Skipping" in result.stdout:
            shutil.move(os.path.join(folder_path, file), os.path.join(trash_path, file))
            safe_print(f"⏭️ Вже є: {file}")

        else:
            safe_print(f"❌ Не знайдено / Помилка: {file}")
            # safe_print(f"Debug Info: {result.stderr}") # Розкоментуйте, якщо хочете бачити помилки

    except Exception as e:
        safe_print(f"❌ Critical Err: {e}")

    # 2. АНТИ-БАН ПАУЗА після завершення
    wait_time = random.uniform(MIN_DELAY, MAX_DELAY)
    safe_print(f"💤 Пауза {wait_time:.1f}с...")
    time.sleep(wait_time)


# --- ОБРОБКА YOUTUBE (YT-DLP) ---

def download_youtube(url):
    ensure_folders()
    safe_print(f"\n--- 🔴 YouTube Downloader ---")
    safe_print("1. 🎵 MP3 (Audio only)")
    safe_print("2. 🎬 MP4 (Video + Audio)")
    choice = input(">> ").strip()

    if choice == '2':
        save_path = VIDEO_DIR
        fmt = 'bestvideo+bestaudio/best'
    else:
        save_path = MUSIC_DIR
        fmt = 'bestaudio/best'

    # Налаштування yt-dlp
    ydl_opts = {
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'format': fmt,
        'noplaylist': True,
        'nocheckcertificate': True,
        'nooverwrites': True,
        'quiet': False,
    }

    # Додавання аудіо-конвертації для MP3
    if choice != '2':
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'] = [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ]

    # Додавання Cookies
    if get_cookies_path():
        ydl_opts['cookiefile'] = get_cookies_path()

    # Додавання PROXY
    proxy = get_random_proxy()
    if proxy:
        ydl_opts['proxy'] = proxy
        safe_print(f"🕵️ Використовую Proxy: Так")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        safe_print(f"❌ Помилка завантаження: {e}")


def process_spotify_or_search(query):
    ensure_folders()
    output_tmpl = os.path.join(MUSIC_DIR, "{artist} - {title}.{output-ext}")

    command = ["spotdl", query, "--output", output_tmpl, "--overwrite", "skip"]
    if get_cookies_path(): command.extend(["--cookie-file", get_cookies_path()])

    # Proxy для прямого пошуку
    proxy = get_random_proxy()
    if proxy: command.extend(["--proxy", proxy])

    safe_print(f"\n--- 🎵 Пошук/Link: {query} ---")
    try:
        subprocess.run(command, check=True, encoding='utf-8', errors='ignore')
        # Чистка номерів треків
        for fname in os.listdir(MUSIC_DIR):
            if fname.endswith(".mp3"):
                remove_track_number(os.path.join(MUSIC_DIR, fname))
    except Exception as e:
        safe_print(f"❌ Помилка: {e}")


def upgrade_local_files_parallel():
    ensure_folders()
    print("\n" + "=" * 40)
    print("🚀 МАСОВЕ ОНОВЛЕННЯ (Smart Anti-Ban)")
    print("=" * 40)

    folder_path = input("📂 Перетягніть сюди папку зі старими треками: ").strip().strip('"')
    if not os.path.exists(folder_path):
        print("❌ Папка не знайдена.")
        return

    trash_path = os.path.join(folder_path, "OLD_TRASH")
    if not os.path.exists(trash_path): os.makedirs(trash_path)

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.m4a', '.wav'))]
    if not files:
        print("⚠️ Папка порожня або немає музики.")
        return

    print(f"\nЗнайдено файлів: {len(files)}")
    print("-" * 30)
    print("⚠️ УВАГА: Щоб уникнути бану, не ставте багато потоків.")
    print("✅ Рекомендовано: 1-2 (якщо немає проксі), 3-5 (якщо є список проксі)")
    print("-" * 30)

    # --- ЦИКЛ ВВОДУ ПОТОКІВ ---
    while True:
        try:
            w_input = input("Кількість потоків (Enter = 2): ").strip()
            if not w_input:
                mw = 2
                break
            mw = int(w_input)
            if mw > 0: break
            print("Число має бути > 0")
        except ValueError:
            print("❌ Введіть число.")

    print(f"\n🚀 СТАРТ ({mw} потоків). Зачекайте...")

    if not PROXY_LIST:
        print("⚠️ УВАГА: Проксі не задані. Будуть використовуватись великі паузи.")

    with ThreadPoolExecutor(max_workers=mw) as executor:
        futures = [executor.submit(process_single_file_task, f, folder_path, trash_path) for f in files]
        for f in futures: f.result()

    print(f"\n✅ Завершено! Музика тут: {MUSIC_DIR}")


def main():
    print(f"\n=== 🎵 BOT v11.0 (PRO: Proxy + Anti-Ban) 🎵 ===")
    ensure_folders()
    if not check_dependencies():
        input("\nНатисніть Enter для виходу...")
        sys.exit()

    if get_cookies_path():
        print("🍪 Cookies: ✅ Знайдено")
    else:
        print("⚠️ Cookies: ❌ Немає (Ліміти будуть суворіші)")

    if PROXY_LIST:
        print(f"🕵️ Proxy: ✅ Завантажено {len(PROXY_LIST)} шт.")
    else:
        print(f"⚠️ Proxy: ❌ Список порожній (Використовується ваша IP)")

    while True:
        print("\n1. 📥 Скачати (Link / Search)")
        print("2. ♻️ Масове оновлення папки (Upgrade)")
        print("q. Вихід")
        choice = input(">> ").strip()
        if choice.lower() == 'q': break

        if choice == '1':
            q = input("Посилання або назва пісні: ").strip()
            if not q: continue

            if "youtube.com" in q or "youtu.be" in q:
                download_youtube(q)
            else:
                process_spotify_or_search(q)

        elif choice == '2':
            upgrade_local_files_parallel()

        # Швидкий ввід посилань в меню
        elif len(choice) > 5:
            if "youtube" in choice:
                download_youtube(choice)
            else:
                process_spotify_or_search(choice)


if __name__ == "__main__":
    main()
