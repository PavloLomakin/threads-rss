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

    # Каждый пост начинается с большого блока div.x1a6qonq
    for post_block in soup.find_all("div", class_="x1a6qonq"):
        # 1) Собираем текст поста
        text_parts = post_block.find_all("span")
        full_text = "\n".join(
            span.get_text(strip=True)
            for span in text_parts
            if span.get_text(strip=True)
        )

        if not full_text:
            continue

        # 2) Ищем ссылку на пост
        link_tag = post_block.find("a", href=True)
        if link_tag:
            post_url = "https://www.threads.net" + link_tag["href"]
        else:
            post_url = BASE_URL

        # 3) Ищем дату публикации
        time_tag = post_block.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            pub_date = datetime.fromisoformat(
                time_tag["datetime"].replace("Z", "+00:00")
            )
        else:
            pub_date = datetime.now(timezone.utc)

        posts.append({
            "title": full_text[:80] + ("..." if len(full_text) > 80 else ""),
            "description": full_text,
            "link": post_url,
            "pub_date": pub_date,
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
    try:
        html = fetch_threads_profile_html()
        print("✅ HTML получен")

        posts = parse_posts_from_html(html)
        print(f"✅ Найдено постов: {len(posts)}")

        if not posts:
            print("⚠️ Посты не найдены — возможно, структура Threads изменилась или профиль пустой.")
            return

        generate_rss(posts)
        print(f"✅ RSS сгенерирован: {OUTPUT_PATH}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")



if __name__ == "__main__":
    main()
