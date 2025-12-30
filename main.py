print("🚀 main.py est bien exécuté")

import feedparser
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter
import re
generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


STOP_WORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "en", "à",
    "pour", "dans", "sur", "au", "aux", "par", "avec", "ce", "ces",
    "est", "sont", "plus", "moins", "que", "qui", "dont", "entre",
    "direct", "images", "année", "nouvelle", "leurs", "être"
}


def fetch_articles():
    sources = {
        "Le Monde": "https://www.lemonde.fr/rss/une.xml",
        "Sud Ouest": "https://www.sudouest.fr/rss.xml",
        "Courrier International": "https://www.courrierinternational.com/feed/all/rss.xml"
    }

    articles_by_source = {}
    limit = datetime.now(timezone.utc) - timedelta(hours=24)

    for source, url in sources.items():
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries:
            if hasattr(entry, "published_parsed"):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published < limit:
                    continue

            articles.append({
                "title": entry.title,
                "link": entry.link
            })

        articles_by_source[source] = articles

    return articles_by_source

def generate_ai_summary(articles_by_source):
    words = []

    for articles in articles_by_source.values():
        for article in articles:
            title = article["title"].lower()
            title = re.sub(r"[^\w\s]", "", title)

            for word in title.split():
                if (
                    len(word) > 3
                    and word.isalpha()
                    and word not in STOP_WORDS
                ):
                    words.append(word)

    if not words:
        return (
            "L’actualité des dernières 24 heures est relativement calme, "
            "sans thème dominant clairement identifiable."
        )

    counter = Counter(words)
    common = counter.most_common(6)
    themes = ", ".join(word for word, _ in common)

    return (
        f"L’actualité des dernières 24 heures est marquée par plusieurs thèmes forts, "
        f"notamment : {themes}. "
        "Ces sujets reflètent à la fois les tensions internationales, "
        "les débats politiques et les dynamiques culturelles du moment."
    )


def generate_html(articles_by_source, summary):
    print("🧠 generate_html() appelée")

    from datetime import datetime, timezone
    from pathlib import Path

    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    print("⏱ Heure générée :", generated_at)

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Briefing Actus</title>
</head>
<body>

<h1>🗞️ Briefing Actus</h1>

<p style="color: gray; font-size: 0.9em;">
Dernière mise à jour : {generated_at}
</p>

<h2>🧠 Analyse & contexte</h2>
<p>{summary}</p>
"""

    for source, articles in articles_by_source.items():
        html += f"<h2>{source}</h2>"
        for article in articles:
            html += f'<p><a href="{article["link"]}">{article["title"]}</a></p>'

    html += "</body></html>"

    output_path = Path("index.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("📄 Écriture de index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Fichier écrit")

if __name__ == "__main__":
    articles = fetch_articles()
    summary = generate_ai_summary(articles)
    generate_html(articles, summary)
