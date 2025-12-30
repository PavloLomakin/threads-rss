import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

# ------------ НАСТРОЙКИ ------------
THREADS_USERNAME = "pavlo.lomakin"
BASE_URL = f"https://www.threads.net/@{THREADS_USERNAME}"
MAX_ITEMS = 20
OUTPUT_PATH = "docs/index.xml"
# -----------------------------------

def fetch_threads_profile_html():
    print(f"🔗 Загружаю профиль: {BASE_URL}")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    resp = requests.get(BASE_URL, headers=headers, timeout=20)
    print(f"✅ Ответ Threads: {resp.status_code}")
    resp.raise_for_status()
    return resp.text


import json

def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # 1. Find the embedded JSON
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("❌ JSON script tag not found")
        return []

    try:
        data = json.loads(script_tag.string)
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        return []

    # 2. Navigate to posts inside the JSON
    try:
        posts_data = (
            data["props"]["pageProps"]["userProfile"]["posts"]
        )
    except KeyError:
        print("❌ Posts not found in JSON structure")
        return []

    posts = []
    for post in posts_data[:MAX_ITEMS]:
        text = post.get("caption", "")
        post_id = post.get("id")
        timestamp = post.get("taken_at")

        if not text:
            continue

        # Convert timestamp → datetime
        pub_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        posts.append({
            "title": text[:80] + ("..." if len(text) > 80 else ""),
            "description": text,
            "link": f"{BASE_URL}/post/{post_id}",
            "pub_date": pub_date,
        })

    print(f"📊 Parsed posts from JSON: {len(posts)}")
    return posts



def generate_rss(posts):
    fg = FeedGenerator()
    fg.id(BASE_URL)
    fg.title(f"Threads @{THREADS_USERNAME}")
    fg.link(href=BASE_URL, rel="alternate")
    fg.description(f"RSS лента постов Threads @{THREADS_USERNAME}")

    for post in posts:
        fe = fg.add_entry()
        fe.id(post["link"] + "#" + post["pub_date"].isoformat())
        fe.title(post["title"])
        fe.link(href=post["link"])
        fe.description(post["description"])
        fe.pubDate(post["pub_date"])

    rss_str = fg.rss_str(pretty=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(rss_str)

    print(f"💾 RSS сохранён в {OUTPUT_PATH}")


def main():
    try:
        html = fetch_threads_profile_html()
        print("✅ HTML получен")

        posts = parse_posts_from_html(html)

        # Даже если постов нет — создаём пустой RSS, чтобы GitHub Pages не ломался
        if not posts:
            print("⚠️ Посты не найдены — создаю пустой RSS")
            posts = [{
                "title": "No posts found",
                "description": "Threads did not return any readable content.",
                "link": BASE_URL,
                "pub_date": datetime.now(timezone.utc),
            }]

        generate_rss(posts)
        print(f"🎉 Готово: RSS сгенерирован (постов: {len(posts)})")

    except Exception as e:
        print(f"❌ Ошибка в main(): {e}")


if __name__ == "__main__":
    main()
