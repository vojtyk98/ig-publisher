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

# ========== 📥 Načtení plánu ==========
def load_schedule():
    try:
        response = requests.get(SCHEDULE_URL)
        response.raise_for_status()
        print("✅ JSON načten.")
        return response.json()
    except Exception as e:
        print(f"❌ Chyba načítání JSON: {e}")
        return []

# ========== 🗑️ Smazání souboru z GitHubu ==========
def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
        if sha:
            data = {
                "message": f"delete {filename}",
                "sha": sha,
                "branch": GITHUB_BRANCH
            }
            delete_resp = requests.delete(url, headers=headers, json=data)
            if delete_resp.status_code in (200, 204):
                print(f"🗑️ GitHub: Soubor {filename} smazán.")
    else:
        print(f"⚠️ Soubor {filename} nebyl nalezen (nebo už smazán).")

# ========== 📤 IG Publikace ==========
def publish_ready_ig_posts():
    schedule = load_schedule()
    if not schedule:
        print("📭 Žádné příspěvky k naplánování.")
        return

    now = int(time.time())
    new_schedule = []

    for post in schedule:
        if post["publish_time"] <= now:
            filename = post["filename"]
            image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
            print(f"📤 Publikuji IG: {filename}")
            print(f"🌍 Obrázek: {image_url}")

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

                # 2️⃣ Publikace příspěvku
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
                    print(f"❌ Chyba publikace: {publish_res}")
                    new_schedule.append(post)
            else:
                print(f"❌ Chyba vytvoření containeru: {container_res}")
                new_schedule.append(post)
        else:
            new_schedule.append(post)

    # ========== 📄 Aktualizace JSON ==========
    if new_schedule:
        update_schedule_on_github(new_schedule)
        print("📂 JSON aktualizován na GitHubu.")
    else:
        delete_file_from_github(SCHEDULE_FILENAME)
        print("✅ Vše naplánováno. JSON smazán.")

# ========== ✍️ Uložení nového JSON ==========
def update_schedule_on_github(new_schedule):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{SCHEDULE_FILENAME}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_resp = requests.get(url, headers=headers)
    sha = None
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")

    content = base64.b64encode(json.dumps(new_schedule, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Aktualizace plánovaného JSON",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=data)
    if put_resp.status_code in (200, 201):
        print("✅ JSON úspěšně aktualizován.")
    else:
        print(f"❌ Chyba při aktualizaci JSON: {put_resp.json()}")

# ========== 🏁 Start ==========
if __name__ == "__main__":
    publish_ready_ig_posts()
