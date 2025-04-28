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
SCHEDULE_FOLDER = "NotPlaned"  # složka na GitHubu
SCHEDULE_FOLDER_URL = f"https://vojtyk98.github.io/{GITHUB_REPOSITORY}/{SCHEDULE_FOLDER}/"

# ========== GitHub mazání ==========
def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{SCHEDULE_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
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
        delete_resp = requests.delete(url, headers=headers, json=data)
        if delete_resp.status_code == 200:
            print(f"🗑️ Soubor {filename} smazán z GitHubu.")
        else:
            print(f"❌ Chyba při mazání {filename}: {delete_resp.json()}")
    else:
        print(f"⚠️ Soubor {filename} nebyl nalezen.")

# ========== 📤 Publikace IG ==========
def publish_ready_ig_posts():
    try:
        response = requests.get(SCHEDULE_FOLDER_URL)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Chyba při načítání složky plánů: {e}")
        return

    now = int(time.time())

    # Vypíšeme všechny JSON soubory
    all_files = [line for line in response.text.split('\n') if '.json' in line]
    if not all_files:
        print("ℹ️ Žádné JSON plány nenalezeny.")
        return

    for line in all_files:
        # Vytáhneme jméno souboru z linku
        start = line.find('href="') + len('href="')
        end = line.find('"', start)
        filename = line[start:end]

        if not filename.endswith(".json"):
            continue

        json_url = f"{SCHEDULE_FOLDER_URL}{filename}"
        try:
            post_resp = requests.get(json_url)
            post_resp.raise_for_status()
            post_data = post_resp.json()
        except Exception as e:
            print(f"❌ Chyba načítání JSON souboru {filename}: {e}")
            continue

        publish_time = post_data.get("publish_time")
        image_name = post_data.get("filename")

        if not publish_time or not image_name:
            print(f"⚠️ JSON {filename} neobsahuje publish_time nebo filename.")
            continue

        time_diff = publish_time - now

        if -60 <= time_diff <= 60:
            print(f"🚀 Čas publikace nastal: {image_name}")

            # Vytvoříme container na IG
            image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{SCHEDULE_FOLDER}/{quote(image_name)}"
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
                    print(f"✅ IG publikováno: {image_name}")
                    delete_file_from_github(filename)
                    delete_file_from_github(image_name)
                else:
                    print(f"❌ Chyba při publikaci: {publish_res}")
            else:
                print(f"❌ Chyba při vytvoření containeru: {container_res}")

        else:
            print(f"⏳ {image_name} zatím NEpublikujeme (rozdíl {time_diff} sekund).")

# ========== 🏁 Spuštění ==========
if __name__ == "__main__":
    publish_ready_ig_posts()
