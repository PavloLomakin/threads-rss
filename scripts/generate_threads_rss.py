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


def parse_posts_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    # Threads меняет классы → собираем ВСЕ <span> с текстом
    candidate_spans = soup.find_all("span")
    text_chunks = []

    for span in candidate_spans:
        text = span.get_text(strip=True)
        if text and len(text) > 20:  # фильтр от мусора
            text_chunks.append(text)

    print(f"🔍 Найдено текстовых блоков: {len(text_chunks)}")

    if not text_chunks:
        print("⚠️ Не найдено ни одного текстового блока")
        return []

    # Склеиваем в один большой пост (RSS всё равно читает как ленту)
    full_text = "\n".join(text_chunks[:MAX_ITEMS])

    posts.append({
        "title": full_text[:80] + ("..." if len(full_text) > 80 else ""),
        "description": full_text,
        "link": BASE_URL,
        "pub_date": datetime.now(timezone.utc),
    })

    print(f"📊 Итог: постов для RSS: {len(posts)}")
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
