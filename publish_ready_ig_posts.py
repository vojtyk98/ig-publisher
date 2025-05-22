import os
import time
import json
import requests
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
import base64

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
INSTAGRAM_ID = "17841472710123488"
GH_TOKEN = os.getenv("GH_TOKEN")
GITHUB_REPOSITORY = "scheduler-folder"
GITHUB_USERNAME = "vojtyk98"
GITHUB_BRANCH = "main"
GITHUB_UPLOAD_FOLDER = "NotPlaned"
SCHEDULE_FOLDER_URL = "https://api.github.com/repos/vojtyk98/scheduler-folder/contents/NotPlaned"
TOLERANCE = "600"

API_BASE = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}"
CDN_BASE = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/"

# ========== 🔧 Pomocné funkce ==========

def list_jsons():
    resp = requests.get(API_BASE)
    if resp.status_code == 200:
        return [f for f in resp.json() if f["name"].endswith(".json") and ".done." not in f["name"] and ".error." not in f["name"]]
    else:
        print("[❌] Nelze načíst obsah složky.")
        return []

def download(file_url):
    r = requests.get(file_url)
    return r.json() if r.status_code == 200 else None

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

def rename_file(old_name, suffix):
    url = f"{API_BASE}/{quote(old_name)}"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code != 200:
        print(f"[⚠️] Nelze načíst {old_name} pro přejmenování.")
        return False

    sha = get_resp.json()["sha"]
    content = get_resp.json()["content"]
    decoded = base64.b64decode(content.encode()).decode()
    new_name = old_name.replace(".json", f".{suffix}.json")

    put_resp = requests.put(
        f"{API_BASE}/{quote(new_name)}",
        headers=headers,
        json={
            "message": f"Přejmenování {old_name} → {new_name}",
            "content": base64.b64encode(decoded.encode()).decode(),
            "branch": GITHUB_BRANCH
        }
    )

    if put_resp.status_code in (200, 201):
        delete_resp = requests.delete(url, headers=headers, json={
            "message": f"Delete původního souboru {old_name}",
            "sha": sha,
            "branch": GITHUB_BRANCH
        })
        if delete_resp.status_code in (200, 201):
            print(f"[✅] Přejmenováno na {new_name} a starý smazán.")
            return True
        else:
            print(f"[❌] Přejmenování proběhlo, ale mazání starého selhalo.")
            return False
    else:
        print(f"[❌] Selhalo přejmenování: {put_resp.text}")
        return False

# ========== 🚀 Hlavní běh ==========

def main():
    print("🔄 Načítám naplánované příspěvky...")
    files = list_jsons()
    now = int(datetime.now(timezone.utc).timestamp())

    for f in files:
        name = f["name"]
        print(f"\n🔍 Zpracovávám: {name}")

        data = download(f["download_url"])
        if not data:
            print("[❌] Nelze načíst JSON.")
            continue

        filename = data.get("filename")
        publish_time = data.get("publish_time")
        if not filename or not publish_time:
            print("[⚠️] JSON chybně vyplněn.")
            continue

        if not (publish_time - TOLERANCE <= now <= publish_time + TOLERANCE):
            print(f"⏳ Ještě není čas na publikaci ({publish_time - now} s zbývá)")
            continue

        image_url = f"{CDN_BASE}{quote(filename)}"
        post_id = publish_to_ig(image_url)

        if post_id:
            print(f"🎉 Publikováno! Post ID: {post_id}")
            if rename_file(name, "done"):
                print(f"[🧼] JSON označen jako hotový.")
            else:
                print(f"[❌] Publikace OK, ale přejmenování selhalo.")
                rename_file(name, "error")
        else:
            print(f"[⛔] Publikace se nezdařila.")
            rename_file(name, "error")

if __name__ == "__main__":
    main()
