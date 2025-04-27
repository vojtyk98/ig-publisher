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

# ========== 📂 Funkce GitHub ==========
def list_files_from_github():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Chyba načítání souborů: {response.status_code}")
        return []

def download_file_from_github(filename):
    url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{filename}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None

def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
        if sha:
            data = {"message": f"delete {filename}", "sha": sha, "branch": GITHUB_BRANCH}
            delete_resp = requests.delete(url, headers=headers, json=data)
            if delete_resp.status_code in (200, 204):
                print(f"🗑️ GitHub: {filename} smazán.")
            else:
                print(f"❌ Chyba mazání {filename}: {delete_resp.json()}")

# ========== 📤 Funkce IG publikace ==========
def publish_to_ig(image_filename):
    image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(image_filename)}"
    print(f"🌍 Publikuji obrázek: {image_url}")

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
            print(f"✅ Publikováno {image_filename}")
            return True
        else:
            print(f"❌ Chyba publikace: {publish_res}")
    else:
        print(f"❌ Chyba vytvoření containeru: {container_res}")
    return False

# ========== 🚀 Hlavní logika ==========
def main():
    files = list_files_from_github()
    if not files:
        print("📭 Žádné soubory k publikaci.")
        return

    now = int(time.time())

    for file in files:
        name = file["name"]
        if name.endswith(".json"):
            content = download_file_from_github(name)
            if content:
                data = json.loads(content.decode("utf-8"))
                publish_time = data.get("publish_time")
                filename = data.get("filename")

                if publish_time and filename:
                    if now >= publish_time:
                        success = publish_to_ig(filename)
                        if success:
                            delete_file_from_github(filename)
                            delete_file_from_github(name)  # smaže JSON
                    else:
                        print(f"🕒 {filename} ještě nepublikujeme (čeká).")
                else:
                    print(f"⚠️ JSON {name} neobsahuje potřebná data.")

# ========== 🏁 Spuštění ==========
if __name__ == "__main__":
    main()
