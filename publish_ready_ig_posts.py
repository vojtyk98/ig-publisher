import os
import json
import time
import requests
from urllib.parse import quote
from datetime import datetime

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

SCHEDULE_FILE = os.path.join("NotPlaned", "ig_schedule.json")

# ========== 📂 Načti naplánované příspěvky ==========
def load_schedule():
    json_url = "https://vojtyk98.github.io/scheduler-folder/NotPlaned/ig_schedule.json"
    try:
        response = requests.get(json_url)
        response.raise_for_status()
        print("✅ JSON úspěšně načten z GitHub Pages.")
        return response.json()
    except Exception as e:
        print("❌ Chyba při načítání JSON z GitHub Pages:", e)
        return []

# ========== 🗑️ GitHub mazání ==========
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

# ========== 📤 IG Publikace ==========
def publish_ready_ig_posts():
    try:
        response = requests.get("https://vojtyk98.github.io/scheduler-folder/NotPlaned/ig_schedule.json")
        response.raise_for_status()
        schedule = response.json()
        print("✅ JSON úspěšně načten.")
    except Exception as e:
        print("❌ Chyba při načítání JSON:", e)
        return

    now = int(time.time())
    remaining = []
    published_keys = set()

already_handled = set()

for post in schedule:
    key = (post["filename"], post["publish_time"])
    if key in already_handled:
        continue
    already_handled.add(key)

    if post["publish_time"] <= now:
        filename = post["filename"]
        image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
        print(f"\n📤 Publikuji IG: {filename}")
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
            else:
                print(f"❌ IG chyba při publikaci: {publish_res}")
        else:
            print(f"❌ IG chyba při vytvoření containeru: {container_res}")
    else:
        remaining.append(post)

    # Uložení zpět do JSON přes GitHub API
    if remaining:
        try:
            new_json = json.dumps(remaining, indent=2)
            url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/ig_schedule.json"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            sha = requests.get(url, headers=headers).json().get("sha")

            upload = requests.put(url, headers=headers, json={
                "message": "update schedule",
                "content": base64.b64encode(new_json.encode("utf-8")).decode("utf-8"),
                "branch": GITHUB_BRANCH,
                "sha": sha
            })

            if upload.status_code in (200, 201):
                print("✅ Aktualizovaný JSON nahrán na GitHub.")
            else:
                print(f"❌ Chyba při aktualizaci JSON: {upload.json()}")

        except Exception as e:
            print("❌ Chyba při ukládání zbývajících položek:", e)
    else:
        print("✅ Vše bylo publikováno. JSON bude prázdný.")

# ========== 🏁 Spuštění ==========
if __name__ == "__main__":
    publish_ready_ig_posts()
