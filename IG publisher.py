import os
import time
import requests
import json

# ========== 🔒 Nastavení ==========

ACCESS_TOKEN = "EAAQsUjjteAABO3zZAeyybzfNjbcFCxDH5OJDuzYe2mZAKvWARH5ZBrrgbku972CtNcIVlM9hbyUb3agishZAkfvEZB9zZBSQQnEHIwVZCMLB2TXewgMMMtfdv53tbfmEsxkYaUwDzZCJrTalN6UZC2mY9zPQbAsfycpiSwDEOPeBLR5ePjkZAIgeaGNQl5I5OlyUCYxKPHBSsnRyQ6XFIE"
INSTAGRAM_ID = "17841472710123488"
SCHEDULE_FILE = "ig_schedule.json"

# ========== 📤 Funkce ==========

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, "r") as f:
        return json.load(f)

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2)

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
            else:
                print(f"❌ IG publikace chyba: {res}")
        else:
            remaining.append(post)

    if remaining:
        save_schedule(remaining)
    else:
        # Pokud je seznam prázdný, smažeme JSON
        print("✅ Všechny příspěvky publikovány. Mažu ig_schedule.json.")
        if os.path.exists(SCHEDULE_FILE):
            os.remove(SCHEDULE_FILE)

if __name__ == "__main__":
    publish_ready_ig_posts()
