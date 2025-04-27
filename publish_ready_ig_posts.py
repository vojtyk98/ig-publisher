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

# ===== Funkce =====
def delete_file_from_github(filename):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/contents/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json().get("sha")
        data = {"message": f"delete {filename}", "sha": sha, "branch": GITHUB_BRANCH}
        delete_resp = requests.delete(url, headers=headers, json=data)
        if delete_resp.status_code == 200:
            print(f"🗑️ Soubor {filename} smazán.")
    else:
        print(f"⚠️ Soubor {filename} nebyl nalezen → {resp.status_code}")

def publish_ready_ig_posts():
    try:
        response = requests.get(SCHEDULE_URL)
        response.raise_for_status()
        schedule = response.json()
        print("✅ JSON úspěšně načten.")
    except Exception as e:
        print(f"❌ Chyba při načítání JSON:", e)
        return

    now = int(time.time())
    tolerance = 300  # 5 minut tolerance = 300 sekund
    remaining = []

    for post in schedule:
        publish_time = post["publish_time"]
        filename = post["filename"]

        difference = abs(publish_time - now)

        if difference <= tolerance:
            print(f"📤 Čas publikace nastal pro: {filename}")
            image_url = f"https://cdn.jsdelivr.net/gh/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}@{GITHUB_BRANCH}/{GITHUB_UPLOAD_FOLDER}/{quote(filename)}"
            print(f"🌍 Obrázek: {image_url}")

            # Publikuj na IG
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
                    print(f"❌ Chyba publikace IG: {publish_res}")
                    remaining.append(post)
            else:
                print(f"❌ Chyba vytvoření containeru: {container_res}")
                remaining.append(post)
        else:
            print(f"⏳ {filename} zatím NEpublikujeme (rozdíl {publish_time - now} sekund).")
            remaining.append(post)

    if remaining:
        print(f"⚠️ Některé příspěvky čekají. JSON zůstává.")
    else:
        print("✅ Vše publikováno. JSON bude smazán.")
        delete_file_from_github(SCHEDULE_FILENAME)

# ===== Spuštění =====
if __name__ == "__main__":
    publish_ready_ig_posts()
