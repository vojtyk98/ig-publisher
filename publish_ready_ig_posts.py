import os
import time
import json
import requests
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
GH_TOKE = os.getenv("GH_TOKEN")
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_USERNAME = "vojtyk98"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
SCHEDULE_FOLDER_URL = "https://api.github.com/repos/vojtyk98/scheduler-folder/contents/NotPlaned"

WINDOW = 300  # 5 minut

API_BASE = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}"
CDN_BASE = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/"

# ========== 🔧 Pomocné funkce ==========

def list_jsons():
    resp = requests.get(API_BASE)
    print(f"[📦] Načítám JSONy ze složky: {resp.status_code}")
    if resp.status_code == 200:
        return [f for f in resp.json() if f["name"].endswith(".json")]
    else:
        print("[❌] Nelze načíst obsah složky.")
        return []

def download(file_url):
    r = requests.get(file_url)
    return r.json() if r.status_code == 200 else None

def delete(filename):
    url = f"{API_BASE}/{quote(filename)}"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    print(f"[🧪] Mazání souboru: {filename}")
    get_resp = requests.get(url, headers=headers)
    print(f"[🔍] GET status: {get_resp.status_code}")

    if get_resp.status_code != 200:
        print(f"[⚠️] Soubor {filename} nenalezen.")
        return False

    sha = get_resp.json()["sha"]
    data = {
        "message": f"Delete {filename}",
        "sha": sha,
        "branch": BRANCH
    }
    delete_resp = requests.delete(url, headers=headers, json=data)
    print(f"[🔍] DELETE status: {delete_resp.status_code}")

    if delete_resp.status_code in (200, 201):
        print(f"[✅] Smazán: {filename}")
        return True
    else:
        print(f"[❌] Mazání selhalo: {delete_resp.text}")
        return False

def rename_to_error(filename):
    url = f"{API_BASE}/{quote(filename)}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code != 200:
        print(f"[⚠️] Nelze načíst {filename} pro přejmenování.")
        return

    sha = get_resp.json()["sha"]
    new_name = filename.replace(".json", ".error.json")
    data = {
        "message": f"Přejmenování {filename} → {new_name}",
        "content": get_resp.json()["content"],
        "sha": sha,
        "branch": BRANCH,
        "path": f"{FOLDER}/{new_name}"
    }

    # vytvoří nový soubor
    put_resp = requests.put(f"{API_BASE}/{quote(new_name)}", headers=headers, json=data)
    if put_resp.status_code in (200, 201):
        print(f"[🚧] JSON přejmenován na {new_name} kvůli chybě mazání.")
        delete(filename)
    else:
        print(f"[❌] Přejmenování selhalo: {put_resp.text}")

def publish_to_ig(image_url, caption="#MrJoke"):
    print(f"\n➡️ Posílám na IG: {image_url}")
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": ACCESS_TOKEN}
    )
    container = r.json()
    print(f"🔎 Container: {r.status_code} — {container}")
    if "id" not in container:
        return None

    c_id = container["id"]
    r2 = requests.post(
        f"https://graph.facebook.com/v21.0/{INSTAGRAM_ID}/media_publish",
        data={"creation_id": c_id, "access_token": ACCESS_TOKEN}
    )
    publish = r2.json()
    print(f"🔎 Publish: {r2.status_code} — {publish}")
    return publish.get("id")

# ========== 🚀 Hlavní běh ==========

def main():
    print("🔄 Načítám příspěvky...")
    files = list_jsons()
    now = int(datetime.now(timezone.utc).timestamp())

    for f in files:
        name = f["name"]
        print(f"\n🔍 Zpracovávám: {name}")

        if ".error." in name:
            print(f"⏭️ Přeskočeno (error tag).")
            continue

        data = download(f["download_url"])
        if not data:
            print("[❌] Nelze načíst JSON.")
            continue

        filename = data.get("filename")
        publish_time = data.get("publish_time")
        if not filename or not publish_time:
            print("[⚠️] JSON chybně vyplněn.")
            continue

        if not (publish_time <= now <= publish_time + WINDOW):
            print(f"⏳ Ještě není čas na publikaci ({publish_time - now} s zbývá)")
            continue

        image_url = f"{CDN_BASE}{quote(filename)}"
        post_id = publish_to_ig(image_url)

        if post_id:
            print(f"🎉 Publikováno! Post ID: {post_id}")
            ok_img = delete(filename)
            ok_json = delete(name)

            if not (ok_img and ok_json):
                print("[🚧] Publikace proběhla, ale mazání selhalo.")
                rename_to_error(name)
        else:
            print("[⛔] Publikace se nezdařila.")

if __name__ == "__main__":
    main()
