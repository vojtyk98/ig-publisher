import os
import time
import json
import requests
from urllib.parse import quote

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
GITHUB_USERNAME = "vojtyk98"
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
GITHUB_TOKEN = os.environ["GH_TOKEN"]
SCHEDULE_FILENAME = "ig_schedule.json"
SCHEDULE_URL = f"https://vojtyk98.github.io/{GITHUB_REPOSITORY}/{GITHUB_UPLOAD_FOLDER}/{SCHEDULE_FILENAME}"

def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
        if not sha:
            print(f"❌ SHA nenalezena pro soubor: {filename}")
            return
        data = {
            "message": f"delete {filename}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        }
        delete_resp = requests.delete(url, headers=headers, json=data)
        if delete_resp.status_code == 200:
            print(f"🗑️ GitHub: Soubor {filename} smazán.")
        else:
            print(f"❌ Chyba při mazání {filename}: {delete_resp.status_code} → {delete_resp.json()}")
    else:
        print(f"⚠️ Soubor {filename} nebyl nalezen → {get_resp.status_code}")

# === IG Publikace ===
def publish_ready_ig_posts():
    print("🔁 Načítám plán...")
    try:
        response = requests.get(SCHEDULE_URL)
        response.raise_for_status()
        schedule = response.json()
        print("✅ JSON úspěšně načten.")
    except Exception as e:
        print(f"❌ Chyba při načítání JSON: {e}")
        return

    now = int(time.time())
    remaining = []
    publikovano = False

    for post in schedule:
        print(f"➡️ Kontrola příspěvku: {post['filename']} v {post['publish_time']} (teď: {now})")
        if post["publish_time"] <= now:
            filename = post["filename"]
            image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
            print(f"📤 Publikuji IG: {filename}")
            print(f"🌐 Obrázek: {image_url}")

            # 1️⃣ Vytvoření containeru
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
                    publikovano = True
                else:
                    print(f"❌ Chyba publikace IG: {publish_res}")
                    remaining.append(post)
            else:
                print(f"❌ Chyba vytvoření containeru IG: {container_res}")
                remaining.append(post)
        else:
            remaining.append(post)

    if remaining:
        print(f"⏳ Některé příspěvky čekají. JSON zůstává.")
    else:
        print("✅ Vše publikováno. JSON bude smazán.")
        delete_file_from_github(SCHEDULE_FILENAME)

# Spuštění
if __name__ == "__main__":
    publish_ready_ig_posts()
