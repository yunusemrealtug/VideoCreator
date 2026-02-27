from bs4 import BeautifulSoup
import json
import requests
import time
import os
import re
from playwright.sync_api import sync_playwright

# ==============================
# DOSYA AYARLARI
# ==============================
year = "1950"

INPUT_FILE = "site_htmls/"+year[2:]+"s.txt"
OUTPUT_FILE = "datas/top100"+year+".json"
POSTER_DIR = "posters/posters"+year+"s"

INPUT_FILE = "site_htmls/bestpictures.txt"
OUTPUT_FILE = "datas/top100BestPicture.json"
POSTER_DIR = "posters/postersBestPictures"


os.makedirs(POSTER_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

download_session = requests.Session()
download_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
})


# ==============================
# HTML OKU (ANA LİSTE)
# ==============================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
movie_blocks = soup.select("li.ipc-metadata-list-summary-item")


movies = []


# ==============================
# VERİ TOPLA (ANA SAYFA)
# ==============================
for movie in movie_blocks:

    title_tag = movie.select_one(".ipc-title__text")
    link_tag = movie.select_one("a.ipc-title-link-wrapper")

    if not title_tag or not link_tag:
        continue

    title = title_tag.text.strip()
    if "." in title:
        title = title.split(".", 1)[1].strip()

    imdb_id = link_tag["href"].split("/")[2]

    imdb_tag = movie.select_one(".ipc-rating-star--rating")
    if not imdb_tag:
        continue
    imdb_score = float(imdb_tag.text.strip())

    votes_tag = movie.select_one(".ipc-rating-star--voteCount")
    if not votes_tag:
        continue

    votes_text = votes_tag.text.strip().strip("()")
    if "K" in votes_text:
        votes = int(float(votes_text.replace("K", "")) * 1_000)
    elif "M" in votes_text:
        votes = int(float(votes_text.replace("M", "")) * 1_000_000)
    else:
        votes = int(votes_text.replace(",", ""))

    metascore_tag = movie.select_one(".metacritic-score-box")
    if not metascore_tag:
        continue

    metascore_10 = int(metascore_tag.text.strip()) / 10
    score = round((imdb_score + metascore_10) / 2, 2)

    movies.append({
        "title": title,
        "imdb_id": imdb_id,
        "score": str(score),
        "votes": votes
    })

# ==============================
# SIRALA & TOP 100
# ==============================
movies.sort(key=lambda x: (x["score"], x["votes"]), reverse=True)

top101 = movies[:101]
top101 = [m for m in top101 if m["title"] != "Hamilton"]
top100 = top101[:100]
top100.reverse()  # 100 → 1

# ==============================
# POSTER URL (YÜKSEK ÇÖZÜNÜRLÜK)
# ==============================
def extract_highres_poster(soup):
    img = soup.select_one("img.ipc-image")
    if not img or not img.get("src"):
        print("Bulama")
        return ""

    src = img["src"]
    poster_ux1000 = re.sub(
        r'@._V1_.*\.jpg',
        '@._V1_UX1000_.jpg',
        src
    )

    return poster_ux1000

# ==============================
# POSTER İNDİR
# ==============================
def download_image(url, filename):
    if not url:
        return

    r = download_session.get(url, stream=True, timeout=15)
    if r.status_code != 200:
        return

    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)


# ==============================
# IMDb DETAIL → YÖNETMEN, OYUNCU, POSTER
# ==============================

def save_partial(result):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)



def fetch_credits_playwright(page, imdb_id):
    url = f"https://www.imdb.com/title/{imdb_id}/"
    
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"[WARN] Goto failed for {imdb_id}: {e}")
        page.goto(url, wait_until="networkidle", timeout=30000)


    soup = BeautifulSoup(page.content(), "html.parser")

    developer = ""
    second = third = fourth = ""

    items = soup.find_all("li", attrs={"data-testid": "title-pc-principal-credit"})

    for item in items:
        label_span = item.find("span", class_="ipc-metadata-list-item__label")
        label_a = item.find("a", class_="ipc-metadata-list-item__label--link")

        label = ""
        if label_span:
            label = label_span.get_text(strip=True)
        elif label_a:
            label = label_a.get_text(strip=True)

        if label in ("Director", "Directors"):
            names = [
                a.get_text(strip=True)
                for a in item.select("a.ipc-metadata-list-item__list-content-item")
            ]
            developer = ", ".join(names)

        if label == "Stars":
            stars = [
                a.get_text(strip=True)
                for a in item.select("a.ipc-metadata-list-item__list-content-item")
            ]
            if len(stars) > 0: second = stars[0]
            if len(stars) > 1: third = stars[1]
            if len(stars) > 2: fourth = stars[2]

    poster_url = extract_highres_poster(soup)

    return developer, second, third, fourth, poster_url


# ==============================
# JSON OLUŞTUR + POSTERLERİ KAYDET
# ==============================
result = []
total = len(top100)

result = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )

    for idx, movie in enumerate(top100, start=1):
        rank = total - idx + 1

        try:
            
            data = fetch_credits_playwright(page, movie["imdb_id"])
            if data is None:
                raise RuntimeError("fetch failed")

            developer, second, third, fourth, poster_url = data

            if poster_url:
                poster_file = f"{POSTER_DIR}/{rank}.jpg"
                download_image(poster_url, poster_file)
            

            result.append({
                "year": rank,
                "score": movie["score"],
                "title": movie["title"],
                "developer": developer,
                "second": second,
                "third": third,
                "fourth": fourth
            })

            print(f"{rank}. {movie['title']} ✔")

        except Exception as e:
            print(f"[ERROR] {movie['title']} ({movie['imdb_id']}): {e}")

            # 🔥 KRİTİK SATIR
            save_partial(result)

            continue  # bir sonrakine geç

    browser.close()

save_partial(result)



# ==============================
# JSON YAZ
# ==============================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\nTamamlandı ✔")
