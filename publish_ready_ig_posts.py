import os
import time
import json
import base64
import requests
from urllib.parse import quote
from datetime import datetime

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_USERNAME = "vojtyk98"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
SCHEDULE_FOLDER_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}"

# ====== POMOCNÉ FUNKCE ======
def sanitize_filename(name):
    name = name.strip().replace(" ", "_")
    return "".join(c for c in name if c.isalnum() or c in ("_", ".", "-"))

def list_schedule_files():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(SCHEDULE_FOLDER_URL, headers=headers)
    if response.status_code == 200:
        return [item["name"] for item in response.json() if item["name"].endswith(".json")]
    else:
        print("❌ Chyba při načítání složky plánů:", response.text)
        return []

def load_schedule_file(filename):
    url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{filename}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Chyba při načítání {filename}:", e)
        return None

def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
        data = {
            "message": f"delete {filename}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        }
        delete_resp = requests.delete(url, headers=headers, json=data)
        if delete_resp.status_code == 200:
            print(f"🗑️ {filename} smazán z GitHubu.")
        else:
            print(f"❌ Chyba při mazání {filename}:", delete_resp.text)
    else:
        print(f"⚠️ Soubor {filename} nebyl nalezen → {get_resp.status_code}")

# ====== HLAVNÍ FUNKCE ======
def publish_ready_ig_posts():
    now = int(time.time())
    filenames = list_schedule_files()

    for schedule_file in filenames:
        post = load_schedule_file(schedule_file)
        if not post:
            continue

        publish_time = post.get("publish_time")
        filename = sanitize_filename(post.get("filename", ""))

        if not publish_time or not filename:
            print(f"⚠️ Neplatná data v souboru {schedule_file}")
            continue

        if now < publish_time:
            diff = publish_time - now
            print(f"⏳ {filename} zatím NEpublikujeme (rozdíl {diff} sekund).")
            continue

        image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
        print(f"📸 Čas publikace nastal pro: {filename}")
        print(f"🌐 Obrázek: {image_url}")

        container_res = requests.post(
            f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media",
            data={
                "image_url": image_url,
                "caption": "#MrJoke",
                "access_token": ACCESS_TOKEN
            }
        ).json()

        if "id" in container_res:
            container_id = container_res["id"]
            publish_res = requests.post(
                f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": ACCESS_TOKEN
                }
            ).json()

            if "id" in publish_res:
                print(f"✅ IG publikováno: {filename}")
                delete_file_from_github(filename)
                delete_file_from_github(schedule_file)
            else:
                print(f"❌ Chyba publikace IG: {publish_res}")
        else:
            print(f"❌ Chyba vytvoření containeru: {container_res}")

# ====== SPUŠTĚNÍ ======
if __name__ == "__main__":
    publish_ready_ig_posts()
