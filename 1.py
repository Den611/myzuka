import yt_dlp
import os
import subprocess
import sys
import shutil
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# --- 🔧 ФІКС КОДУВАННЯ ---
sys.stdout.reconfigure(encoding='utf-8')

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


# --- ФУНКЦІЇ ---

def safe_print(msg):
    with print_lock:
        try:
            print(msg)
        except:
            print(msg.encode('ascii', 'ignore').decode('ascii'))


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
        safe_print(f"❌ Не вистачає: {', '.join(missing)}")
        return False
    return True


def ensure_folders():
    if not os.path.exists(MUSIC_DIR): os.makedirs(MUSIC_DIR)
    if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)


def clean_filename_for_search(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace("_", " ").strip()
    return name


# --- ОБРОБКА ФАЙЛІВ ---

def process_single_file_task(file, folder_path, trash_path):
    search_query = clean_filename_for_search(file)
    output_format = os.path.join(MUSIC_DIR, "{artist} - {title}.{output-ext}")

    # max-retries 3 - пробує 3 рази, якщо помилка мережі
    command = ["spotdl", search_query, "--output", output_format, "--overwrite", "skip", "--max-retries", "3"]
    if get_cookies_path(): command.extend(["--cookie-file", get_cookies_path()])

    try:
        files_before = set(os.listdir(MUSIC_DIR))
        result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='ignore')
        files_after = set(os.listdir(MUSIC_DIR))
        new_files = files_after - files_before

        if new_files:
            new_file_name = list(new_files)[0]
            remove_track_number(os.path.join(MUSIC_DIR, new_file_name))
            shutil.move(os.path.join(folder_path, file), os.path.join(trash_path, file))
            safe_print(f"✅ Оновлено: {file}")

        elif "Skipping" in result.stdout:
            shutil.move(os.path.join(folder_path, file), os.path.join(trash_path, file))
            safe_print(f"⏭️ Вже є: {file}")

        else:
            safe_print(f"❌ Пропуск (не знайдено або бан): {file}")

    except Exception as e:
        safe_print(f"❌ Err: {e}")


def download_youtube(url):
    ensure_folders()
    safe_print(f"\n--- 🔴 YouTube ---")
    safe_print("1. 🎵 MP3")
    safe_print("2. 🎬 MP4")
    choice = input(">> ").strip()

    if choice == '2':
        save_path = VIDEO_DIR
        fmt = 'bestvideo+bestaudio/best'
    else:
        save_path = MUSIC_DIR
        fmt = 'bestaudio/best'

    ydl_opts = {
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'format': fmt,
        'noplaylist': True,
        'nocheckcertificate': True,
        'nooverwrites': True,
        'quiet': False,
    }

    if choice != '2':
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'] = [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ]

    if get_cookies_path(): ydl_opts['cookiefile'] = get_cookies_path()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        safe_print(f"❌ Помилка: {e}")


def process_spotify_or_search(query):
    ensure_folders()
    output_tmpl = os.path.join(MUSIC_DIR, "{artist} - {title}.{output-ext}")
    command = ["spotdl", query, "--output", output_tmpl, "--overwrite", "skip"]
    if get_cookies_path(): command.extend(["--cookie-file", get_cookies_path()])

    safe_print(f"\n--- 🎵 Пошук: {query} ---")
    try:
        subprocess.run(command, check=True, encoding='utf-8', errors='ignore')
        for fname in os.listdir(MUSIC_DIR):
            if fname.endswith(".mp3"):
                remove_track_number(os.path.join(MUSIC_DIR, fname))
    except Exception as e:
        safe_print(f"❌ Помилка: {e}")


def upgrade_local_files_parallel():
    ensure_folders()
    print("\n" + "=" * 40)
    print("🚀 МАСОВЕ ОНОВЛЕННЯ МУЗИКИ")
    print("=" * 40)

    folder_path = input("📂 Вставте шлях до старої папки: ").strip().strip('"')
    if not os.path.exists(folder_path):
        print("❌ Папка не знайдена.")
        return

    trash_path = os.path.join(folder_path, "OLD_TRASH")
    if not os.path.exists(trash_path): os.makedirs(trash_path)

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp3', '.m4a', '.wav'))]
    if not files:
        print("⚠️ Папка порожня.")
        return

    print(f"\nЗнайдено файлів: {len(files)}")
    print("-" * 30)
    print("Вкажіть кількість потоків (одночасних завантажень):")
    print("🐢 1-3 : Повільно, але надійно (якщо немає cookies)")
    print("🚗 4-8 : Оптимально (рекомендовано)")
    print("🚀 10+ : ТУРБО (Тільки якщо є cookies.txt!)")
    print("-" * 30)

    # --- ЦИКЛ ВВОДУ ПОТОКІВ ---
    while True:
        try:
            w_input = input("Введіть число (наприклад, 5): ").strip()
            if not w_input:
                mw = 5
                print("Використовую стандарт: 5 потоків.")
                break

            mw = int(w_input)
            if mw > 0:
                break
            else:
                print("Число має бути більше 0.")
        except ValueError:
            print("❌ Це не число. Спробуйте ще раз.")

    print(f"\n🚀 ЗАПУСК {mw} ПОТОКІВ... Поїхали!")

    with ThreadPoolExecutor(max_workers=mw) as executor:
        futures = [executor.submit(process_single_file_task, f, folder_path, trash_path) for f in files]
        for f in futures: f.result()

    print(f"\n✅ Оновлення завершено. Перевірте папку: {MUSIC_DIR}")


def main():
    print(f"=== 🎵 BOT v10.0 (User Control) 🎵 ===")
    ensure_folders()
    if not check_dependencies(): sys.exit()

    if get_cookies_path():
        print("🍪 Cookies: Є")
    else:
        print("⚠️ Cookies немає")

    while True:
        print("\n1. Завантажити (YouTube/Spotify)")
        print("2. 🚀 Масове оновлення (З вибором швидкості)")
        print("q. Вихід")
        choice = input(">> ").strip()
        if choice == 'q': break

        if choice == '1':
            q = input("Введіть посилання/назву: ").strip()
            if "youtube" in q or "youtu.be" in q:
                download_youtube(q)
            else:
                process_spotify_or_search(q)
        elif choice == '2':
            upgrade_local_files_parallel()
        elif len(choice) > 3:
            if "youtube" in choice:
                download_youtube(choice)
            else:
                process_spotify_or_search(choice)


if __name__ == "__main__":
    main()