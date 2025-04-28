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

# ===== Pomocné funkce =====
def get_schedule_files():
    """Stáhne seznam všech JSON souborů v plánovací složce."""
    response = requests.get(SCHEDULE_FOLDER_URL)
    response.raise_for_status()
    files = response.json()
    return [f for f in files if f["name"].endswith(".json")]

def download_json(file_url):
    """Stáhne a načte JSON plán."""
    response = requests.get(file_url)
    response.raise_for_status()
    return response.json()

def delete_file(filename):
    """Smaže soubor z GitHubu."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {"Authorization": f"token {os.getenv('GH_TOKEN')}"}
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
        delete_resp = requests.delete(url, headers=headers, json={
            "message": f"Delete {filename}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        })
        if delete_resp.status_code in (200, 201):
            print(f"🗑️ Soubor {filename} smazán.")
        else:
            print(f"❌ Chyba mazání {filename}: {delete_resp.text}")

def publish_to_instagram(image_url, caption="#MrJoke"):
    """Publikuje obrázek na Instagram."""
    container = requests.post(
        f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN
        }
    ).json()

    if "id" not in container:
        print(f"❌ Chyba vytvoření containeru: {container}")
        return None

    container_id = container["id"]
    publish = requests.post(
        f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN
        }
    ).json()

    if "id" in publish:
        print(f"✅ Úspěšně publikováno: {publish['id']}")
        return True
    else:
        print(f"❌ Chyba publikace: {publish}")
        return False

# ===== Hlavní logika =====
def main():
    print("🔄 Načítám seznam plánovaných příspěvků...")
    try:
        files = get_schedule_files()
    except Exception as e:
        print(f"❌ Chyba načítání složky plánů: {e}")
        return

    for file in files:
        try:
            schedule = download_json(file["download_url"])
        except Exception as e:
            print(f"❌ Chyba stahování plánu {file['name']}: {e}")
            continue

        filename = schedule.get("filename")
        publish_time = schedule.get("publish_time")

        if not filename or not publish_time:
            print(f"⚠️ Chybný formát plánu: {file['name']}")
            continue

        now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))  # Český čas UTC+2
        current_timestamp = int(now.timestamp())

        if current_timestamp >= publish_time:
            print(f"📤 Čas publikace nastal: {filename}")
            image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"

            success = publish_to_instagram(image_url)

            if success:
                delete_file(filename)
                delete_file(file["name"])
        else:
            rozdil = publish_time - current_timestamp
            print(f"⏳ {filename} zatím NEpublikujeme (rozdíl {rozdil} sekund).")

# ===== Spuštění =====
if __name__ == "__main__":
    main()
