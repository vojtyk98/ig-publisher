import os
import json
import time
import requests
from urllib.parse import quote

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
SCHEDULE_FILE = "ig_schedule.json"

# GitHub nastavení (pro mazání souborů)
GITHUB_USERNAME = "vojtyk98"
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ========== Načtení plánovaných příspěvků ==========
def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2)

# ========== GitHub mazání ==========
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
            print(f"❌ SHA nenalezen pro soubor: {filename}")
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

# ========== IG Publikace ==========
def publish_ready_ig_posts():
    schedule = load_schedule()
    now = int(time.time())
    remaining = []

    for post in schedule:
        if post["publish_time"] <= now:
            print(f"📤 Publikuji IG: {post['filename']}")
            res = requests.post(
                f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media_publish",
                data={
                    "creation_id": post["container_id"],
                    "access_token": ACCESS_TOKEN
                }
            ).json()

            if "id" in res:
                print(f"✅ IG publikováno: {post['filename']}")
                delete_file_from_github(post["filename"])
            else:
                print(f"❌ IG chyba: {res}")
        else:
            remaining.append(post)

    if remaining:
        save_schedule(remaining)
    else:
        if os.path.exists(SCHEDULE_FILE):
            os.remove(SCHEDULE_FILE)
        print("✅ Vše hotovo. ig_schedule.json smazán.")

# ========== Spuštění ==========
if __name__ == "__main__":
    publish_ready_ig_posts()
