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
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    resp = requests.get(BASE_URL, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    for idx, meta in enumerate(soup.find_all("meta", attrs={"property": "og:description"})):
        content = meta.get("content", "").strip()
        if not content:
            continue

        post_url = BASE_URL

        posts.append({
            "title": content[:80] + ("..." if len(content) > 80 else ""),
            "description": content,
            "link": post_url,
            "pub_date": datetime.now(timezone.utc),
        })

        if len(posts) >= MAX_ITEMS:
            break

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

def main():
    html = fetch_threads_profile_html()
    posts = parse_posts_from_html(html)
    generate_rss(posts)
    print(f"RSS сгенерирован: {OUTPUT_PATH} ({len(posts)} постов)")

if __name__ == "__main__":
    main()
