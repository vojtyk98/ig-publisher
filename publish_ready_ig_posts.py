import os
import time
import json
import base64
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

SCHEDULE_FILE = os.path.join("NotPlaned", "ig_schedule.json")

SCHEDULE_URL = f"https://vojtyk98.github.io/{GITHUB_REPOSITORY}/{SCHEDULE_FILE}"

# ========== 🧹 GitHub mazání ==========
def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {os.environ['GH_TOKEN']}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json()["sha"]
        data = {
            "message": f"delete {filename}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        }
        del_resp = requests.delete(url, headers=headers, json=data)
        if del_resp.status_code == 200:
            print(f"🗑️ GitHub: Soubor {filename} smazán.")
        else:
            print(f"❌ Chyba při mazání {filename}: {del_resp.status_code}")
    else:
        print(f"⚠️ Soubor {filename} nenalezen.")

def upload_schedule_to_github(remaining_schedule):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{SCHEDULE_FILENAME}"
    headers = {
        "Authorization": f"token {os.environ['GH_TOKEN']}",
        "Accept": "application/vnd.github.v3+json"
    }

    if not remaining_schedule:
        delete_file_from_github(SCHEDULE_FILENAME)
        return

    content = base64.b64encode(json.dumps(remaining_schedule, indent=2).encode("utf-8")).decode("utf-8")
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    data = {
        "message": "update schedule after publishing",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=data)
    if put_resp.status_code in (200, 201):
        print("✅ JSON aktualizován na GitHubu.")
    else:
        print(f"❌ Chyba při aktualizaci JSON: {put_resp.json()}")

# ========== Publikace ==========
def publish_ready_ig_posts():
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
    seen = set()

    for post in schedule:
        key = (post["filename"], post["publish_time"])
        if key in seen:
            continue
        seen.add(key)

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
        # NIC NEPŘIDÁVAT do remaining
    else:
        print(f"❌ IG chyba při publikaci: {publish_res}")
        remaining.append(post)
else:
    print(f"❌ IG chyba při vytvoření containeru: {container_res}")
    remaining.append(post)


    upload_schedule_to_github(remaining)

    # 🧹 Smazání lokálního JSONu
    if os.path.exists(LOCAL_JSON_PATH):
        try:
            os.remove(LOCAL_JSON_PATH)
            print("🧹 Lokální JSON smazán.")
        except Exception as e:
            print(f"⚠️ Nepodařilo se smazat lokální JSON: {e}")

# ========== Spuštění ==========
if __name__ == "__main__":
    publish_ready_ig_posts()
