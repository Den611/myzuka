import yt_dlp
import os
import subprocess
import sys
import shutil
import re
import time
import requests
from threading import Lock
import json

# --- 🔧 НАЛАШТУВАННЯ ---
sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔥 ГОЛОВНА ПАПКА
DOWNLOAD_FOLDER = os.path.join(SCRIPT_DIR, "Downloads", "Music")


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
            pass


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


def ensure_folder():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)


def get_existing_songs():
    """Повертає set назв файлів (без розширення) в папці завантажень"""
    if not os.path.exists(DOWNLOAD_FOLDER):
        return set()
    return {os.path.splitext(f)[0].lower() for f in os.listdir(DOWNLOAD_FOLDER)
            if f.endswith(('.mp3', '.m4a', '.ogg', '.opus', '.flac', '.wav', '.mp4'))}


def check_dependencies():
    missing = []
    if not shutil.which("ffmpeg"): missing.append("FFmpeg")
    if missing:
        safe_print(f"❌ Не встановлено: {', '.join(missing)}")
        return False
    return True


# --- 🟢 Парсинг треків зі Spotify (через embed, без API/ключів) ---

def parse_spotify_id(url):
    """Витягує тип (track/playlist/album) та ID зі Spotify URL"""
    m = re.search(r'spotify\.com/(track|playlist|album)/([a-zA-Z0-9]+)', url)
    if m:
        return m.group(1), m.group(2)
    return None, None


def get_spotify_tracks(url):
    """Отримує список треків через embed-сторінку Spotify (без API)"""
    sp_type, sp_id = parse_spotify_id(url)
    if not sp_type:
        print("❌ Невірне Spotify посилання")
        return []

    print(f"📋 Тип: {sp_type}, ID: {sp_id}")
    embed_url = f"https://open.spotify.com/embed/{sp_type}/{sp_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        r = requests.get(embed_url, headers=headers)
        if r.status_code != 200:
            print(f"❌ Spotify embed відповів: {r.status_code}")
            return []

        # Шукаємо JSON з даними в HTML
        m = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">\s*({.+?})\s*</script>', r.text, re.DOTALL)
        if not m:
            print("❌ Не вдалося знайти дані на сторінці embed")
            return []

        data = json.loads(m.group(1))
        tracks = []

        # Навігація по JSON структурі
        entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})

        if sp_type == "track":
            artist = entity.get("subtitle", entity.get("authors", [{}])[0].get("name", "Unknown"))
            title = entity.get("title", entity.get("name", ""))
            if title:
                tracks.append(f"{artist} - {title}")

        else:  # playlist або album
            track_list = entity.get("trackList", [])
            for t in track_list:
                artist = t.get("subtitle", "Unknown").split(",")[0].strip()
                title = t.get("title", "")
                if title:
                    tracks.append(f"{artist} - {title}")

        return tracks

    except Exception as e:
        print(f"❌ Помилка парсингу Spotify: {e}")
        return []


# --- 🟢 SPOTIFY (через YouTube, без акаунту) ---
def download_spotify(url):
    ensure_folder()
    print(f"\n📂 Завантаження Spotify в одну папку...")
    print(f"📂 Шлях: {DOWNLOAD_FOLDER}")

    tracks = get_spotify_tracks(url)
    if not tracks:
        print("❌ Не знайдено треків")
        return

    existing = get_existing_songs()
    new_tracks = []
    skipped = 0
    for track in tracks:
        if track.lower() in existing:
            skipped += 1
        else:
            new_tracks.append(track)

    print(f"🎵 Знайдено {len(tracks)} треків. Нових: {len(new_tracks)}, вже є: {skipped}")
    if not new_tracks:
        print("✅ Всі треки вже завантажені!")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'FFmpegMetadata'}, # Спочатку прописуємо текст
            {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
            {'key': 'EmbedThumbnail'}, # Вшиваємо картинку в самому кінці
        ],
    }

    ok = 0
    fail = 0
    for i, track in enumerate(new_tracks, 1):
        print(f"  [{i}/{len(new_tracks)}] 🎵 {track}")
        downloaded = False
        for search in [f"ytmsearch1:{track}", f"ytsearch1:{track}"]:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(search, download=True)
                    if info and 'entries' in info:
                        info = info['entries'][0]
                    title = info.get('title', track) if info else track
                print(f"          ✅ Збережено: {title}.mp3")
                downloaded = True
                ok += 1
                break
            except Exception:
                continue
        if not downloaded:
            print(f"          ❌ Не вдалося завантажити")
            fail += 1

    print(f"\n🏁 Готово! Завантажено: {ok}, пропущено: {skipped}, помилок: {fail}")


# --- 🔎 YOUTUBE ПОШУК (ВСЕ В ОДНУ КУЧУ) ---
def search_and_download_youtube(query):
    ensure_folder()
    print(f"🔎 Шукаю: '{query}'...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'FFmpegMetadata'}, # Спочатку прописуємо текст
            {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
            {'key': 'EmbedThumbnail'}, # Вшиваємо картинку в самому кінці
        ],
    }

    try:
        with yt_dlp.YoutubeDL({**ydl_opts, 'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if info and 'entries' in info:
                info = info['entries'][0]
            title = info.get('title', query) if info else query

        existing = get_existing_songs()
        if title.lower() in existing:
            print(f"⏭️ Вже є: {title}.mp3")
            return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
        print(f"✅ Збережено: {title}.mp3")
    except Exception as e:
        print(f"❌ Помилка: {e}")


# --- 🔴 YOUTUBE LINK (ВСЕ В ОДНУ КУЧУ) ---
def download_youtube_link(url):
    ensure_folder()
    print("1. 🎵 Тільки звук (MP3)")
    print("2. 🎬 Відео (MP4)")
    choice = input(">> ").strip()

    if choice == '2':
        opts = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
    else:
        opts = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'FFmpegMetadata'}, # Спочатку прописуємо текст
                {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
                {'key': 'EmbedThumbnail'}, # Вшиваємо картинку в самому кінці
            ],
        }

    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', url) if info else url
            ext = "mp3" if choice != '2' else info.get('ext', 'mp4')

        existing = get_existing_songs()
        if title.lower() in existing:
            print(f"⏭️ Вже є: {title}.{ext}")
            return

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        print(f"✅ Збережено: {title}.{ext}")
    except Exception as e:
        print(f"❌ Помилка: {e}")


# --- ГОЛОВНЕ МЕНЮ ---
def main():
    print(f"\n=== 🎵 ONE FOLDER BOT v16.2 (Fix Thumbnails) 🎵 ===")
    print(f"📂 Всі файли будуть тут: {DOWNLOAD_FOLDER}")
    ensure_folder()
    if not check_dependencies(): return

    while True:
        print("\nОБЕРІТЬ ДІЮ:")
        print("1. 🟢 Spotify (Плейлист/Трек) -> В ЗАГАЛЬНУ ПАПКУ")
        print("2. 🔎 YouTube Пошук (Назва)   -> В ЗАГАЛЬНУ ПАПКУ")
        print("3. 🔴 YouTube Посилання       -> В ЗАГАЛЬНУ ПАПКУ")
        print("q. Вихід")

        choice = input(">> ").strip()

        if choice == 'q': break

        if choice == '1':
            url = input("Spotify Link: ").strip()
            if url: download_spotify(url)

        elif choice == '2':
            q = input("Введіть назву: ").strip()
            if q: search_and_download_youtube(q)

        elif choice == '3':
            url = input("YouTube Link: ").strip()
            if url: download_youtube_link(url)


if __name__ == "__main__":
    main()
