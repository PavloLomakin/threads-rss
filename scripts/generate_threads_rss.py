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


- name: Generate RSS feed
        env:
          THREADS_USERNAME: "pavlo.lomakin"
        run: |
          python scripts/generate_threads_rss.py

      - name: Show logs
        run: |
          echo "📄 Содержимое docs/index.xml:"
          cat docs/index.xml || echo "⚠️ Файл index.xml не найден"
