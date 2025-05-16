import os
import time
import json
import requests
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_USERNAME = "vojtyk98"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
SCHEDULE_FOLDER_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}"
WINDOW = 300  # 5min okno

# ===== Pomocné funkce =====

def get_schedule_files():
    response = requests.get(SCHEDULE_FOLDER_URL)
    response.raise_for_status()
    return [f for f in response.json() if f["name"].endswith(".json")]

def download_json(file_url):
    response = requests.get(file_url)
    response.raise_for_status()
    return response.json()

def delete_file(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {"Authorization": f"token {os.getenv('GH_TOKEN')}"}

    print(f"\n🧪 Pokus o mazání přes URL: {url}")
    get_resp = requests.get(url, headers=headers)
    print("🔎 GitHub GET status:", get_resp.status_code)

    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
        delete_resp = requests.delete(url, headers=headers, json={
            "message": f"Delete {filename}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        })
        print("🔎 DELETE status:", delete_resp.status_code)
        print("🔎 DELETE odpověď:", delete_resp.text)

        if delete_resp.status_code in (200, 201):
            print(f"✅ Smazán: {filename}")
        else:
            print(f"❌ Chyba při mazání {filename}: {delete_resp.text}")
    else:
        print(f"⚠️ Soubor {filename} neexistuje nebo nelze najít.")
        print("📩 GitHub odpověď:", get_resp.text)

def publish_to_instagram(image_url, caption="#MrJoke"):
    print(f"\n➡️ Posílám na IG API: {image_url}")
    container_resp = requests.post(
        f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN
        }
    )

    print("🔎 Container response:", container_resp.status_code)
    try:
        container = container_resp.json()
    except:
        print("❌ Nevalidní JSON z containeru.")
        return False

    if "id" not in container:
        print(f"❌ Chyba containeru: {container}")
        return False

    container_id = container["id"]

    publish_resp = requests.post(
        f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN
        }
    )

    print("🔎 Publish response:", publish_resp.status_code)
    try:
        publish = publish_resp.json()
    except:
        print("❌ Nevalidní JSON z publikace.")
        return False

    if "id" in publish:
        print(f"🎉 Publikováno! Post ID: {publish['id']}")
        return True
    else:
        print(f"❌ Chyba při publikaci: {publish}")
        return False

# ===== Hlavní logika =====

def main():
    print("🔄 Načítám seznam naplánovaných příspěvků...")
    try:
        files = get_schedule_files()
    except Exception as e:
        print(f"❌ Chyba při načítání složky: {e}")
        return

    for file in files:
        try:
            schedule = download_json(file["download_url"])
        except Exception as e:
            print(f"❌ Chyba načítání {file['name']}: {e}")
            continue

        filename = schedule.get("filename")
        publish_time = schedule.get("publish_time")

        if not filename or not publish_time:
            print(f"⚠️ Neplatný plán v {file['name']}")
            continue

        now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))  # Čas ČR
        current_timestamp = int(now.timestamp())

        print(f"\n🔍 Zpracovávám: {filename}")
        print(f"🕒 Aktuální čas: {current_timestamp}, plánovaný čas: {publish_time}")

        if publish_time <= current_timestamp <= publish_time + WINDOW:
            print(f"📤 Čas publikace právě teď: {filename}")
            image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"

            try:
                success = publish_to_instagram(image_url)
            except Exception as e:
                print(f"❌ Výjimka při publikaci {filename}: {e}")
                continue

            if success:
                delete_file(filename)
                delete_file(file["name"])
            else:
                print(f"⛔ Publikace selhala. {filename} ponechán pro další pokus.")
        else:
            rozdil = publish_time - current_timestamp
            print(f"⏳ {filename} zatím NEpublikujeme (rozdíl {rozdil} s)")

# ===== Spuštění =====
if __name__ == "__main__":
    main()
