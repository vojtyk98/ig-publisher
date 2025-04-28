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
SCHEDULE_FOLDER_URL = f"https://vojtyk98.github.io/{GITHUB_REPOSITORY}/{GITHUB_UPLOAD_FOLDER}/{SCHEDULE_FILENAME}"

# Funkce pro smazání souboru z GitHubu
def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {os.getenv('GH_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
        if sha:
            data = {
                "message": f"Delete {filename}",
                "sha": sha,
                "branch": GITHUB_BRANCH
            }
            del_resp = requests.delete(url, headers=headers, json=data)
            if del_resp.status_code == 200:
                print(f"🗑️ Soubor {filename} smazán z GitHubu.")
            else:
                print(f"❌ Chyba při mazání {filename}: {del_resp.json()}")
    else:
        print(f"⚠️ Soubor {filename} nebyl nalezen → {get_resp.status_code}")

# Publikace příspěvku na IG
def publish_ig_post(filename, publish_time):
    now = int(time.time())
    if now < publish_time:
        print(f"⌛ Ještě čekáme na {filename} (teď: {now}, plán: {publish_time})")
        return False

    image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    print(f"📤 Publikuji {filename}")

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
            print(f"✅ {filename} publikováno na IG.")
            delete_file_from_github(filename)  # smažeme obrázek
            return True
        else:
            print(f"❌ Chyba při publikaci {filename}: {publish_res}")
            return False
    else:
        print(f"❌ Chyba při vytvoření containeru: {container_res}")
        return False

# Hlavní funkce
def publish_ready_posts():
    try:
        # Najdeme všechny JSON soubory
        files_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}"
        headers = {
            "Authorization": f"token {os.getenv('GH_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        files_resp = requests.get(files_url, headers=headers).json()

        json_files = [file["name"] for file in files_resp if file["name"].endswith(".json")]

        if not json_files:
            print("⚠️ Žádné naplánované JSON soubory.")
            return

        for json_file in json_files:
            json_url = f"{SCHEDULE_FOLDER_URL}{quote(json_file)}"
            json_resp = requests.get(json_url)

            if json_resp.status_code == 200:
                data = json_resp.json()
                filename = data["filename"]
                publish_time = data["publish_time"]

                published = publish_ig_post(filename, publish_time)
                if published:
                    delete_file_from_github(json_file)  # smažeme i jeho plánovací JSON
            else:
                print(f"⚠️ Nelze načíst JSON {json_file}: {json_resp.status_code}")

    except Exception as e:
        print(f"❌ Chyba: {e}")

# Spuštění
if __name__ == "__main__":
    publish_ready_posts()
