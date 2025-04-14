import os
import time
import requests
import json

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
SCHEDULE_FILE = "ig_schedule.json"

# GitHub nastavení (pro mazání souborů)
GITHUB_USERNAME = "vojtyk98"
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
GITHUB_TOKEN = "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"

# ========== 📋 Funkce ==========

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, "r") as f:
        return json.load(f)

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2)

def delete_file_from_github(filename):
    """Smaže soubor z GitHubu."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Získáme SHA souboru
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
        data = {
            "message": f"delete {filename}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        }
        delete_resp = requests.delete(url, headers=headers, json=data)
        if delete_resp.status_code == 200:
            print(f"✅ Smazán soubor z GitHub: {filename}")
        else:
            print(f"❌ Chyba při mazání souboru: {delete_resp.json()}")
    else:
        print(f"❌ Soubor nenalezen pro smazání: {filename}")

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
                # ➡️ Po publikaci smažeme obrázek z GitHubu
                delete_file_from_github(post['filename'])
            else:
                print(f"❌ IG publikace chyba: {res}")
        else:
            remaining.append(post)

    if remaining:
        save_schedule(remaining)
    else:
        # Pokud není co publikovat, smažeme ig_schedule.json
        print("✅ Všechny příspěvky publikovány. Mažu ig_schedule.json.")
        if os.path.exists(SCHEDULE_FILE):
            os.remove(SCHEDULE_FILE)

# ========== 🏁 Hlavní spuštění ==========

if __name__ == "__main__":
    publish_ready_ig_posts()
