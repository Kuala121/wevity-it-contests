"""
위비티(wevity.com) IT 공모전 스크래퍼
Playwright를 사용하여 Cloudflare 우회 후 웹/모바일/IT 카테고리(cidx=6) 수집
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime

BASE_URL = "https://www.wevity.com"
IT_URL   = "https://www.wevity.com/?c=find&s=1&cidx=6"

STATUS_MAP = {
    "ing":    "접수중",
    "soon":   "마감임박",
    "future": "접수예정",
    "end":    "마감",
}


def get_html(page, url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("div.ms-list", timeout=15000)
            return page.content()
        except Exception as e:
            print(f"  [!] 시도 {attempt+1} 실패: {e}")
            time.sleep(2)
    return None


def parse_page(html: str, page_num: int) -> tuple[list, int, bool]:
    soup = BeautifulSoup(html, "lxml")
    contests = []

    items = soup.select("div.ms-list ul.list li:not(.top)")
    for item in items:
        tit_div = item.select_one("div.tit")
        if not tit_div:
            continue

        link_tag = tit_div.select_one("a")
        if not link_tag:
            continue

        stat_span = link_tag.select_one("span.stat")
        badge = stat_span.get_text(strip=True) if stat_span else ""
        if stat_span:
            stat_span.extract()
        title = link_tag.get_text(strip=True)

        href = link_tag.get("href", "")
        full_link = (BASE_URL + href) if href.startswith("?") else href

        sub_tit = tit_div.select_one("div.sub-tit")
        categories = []
        if sub_tit:
            cat_text = sub_tit.get_text(strip=True)
            if "분야 :" in cat_text:
                raw = cat_text.split("분야 :")[-1].strip()
                categories = [c.strip() for c in raw.split(",") if c.strip()]

        organ_div = item.select_one("div.organ")
        organization = organ_div.get_text(strip=True) if organ_div else ""

        day_div = item.select_one("div.day")
        dday = ""
        dday_num = 9999
        status = ""
        status_class = ""

        if day_div:
            day_text = day_div.get_text()
            m = re.search(r"D[-−](\d+)", day_text)
            if m:
                dday = f"D-{m.group(1)}"
                dday_num = int(m.group(1))
            elif "D-0" in day_text:
                dday = "D-0"
                dday_num = 0

            dday_span = day_div.select_one("span.dday")
            if dday_span:
                classes = dday_span.get("class", [])
                status_class = next((c for c in classes if c != "dday"), "")
                status = STATUS_MAP.get(status_class, dday_span.get_text(strip=True))

        read_div = item.select_one("div.read")
        views_str = read_div.get_text(strip=True) if read_div else "0"
        views_num = int(views_str.replace(",", "")) if re.fullmatch(r"[\d,]+", views_str) else 0

        contests.append({
            "title":        title,
            "link":         full_link,
            "badge":        badge,
            "categories":   categories,
            "organization": organization,
            "dday":         dday,
            "dday_num":     dday_num,
            "status":       status,
            "status_class": status_class,
            "views":        views_str,
            "views_num":    views_num,
        })

    raw_count = len(items)

    has_next = False
    navi = soup.select_one("div.list-navi")
    if navi:
        for a in navi.select("a[href]"):
            m = re.search(r"gp=(\d+)", a.get("href", ""))
            if m and int(m.group(1)) > page_num:
                has_next = True
                break

    return contests, raw_count, has_next


def scrape_all(max_pages: int = 70) -> list:
    all_contests = []
    seen_titles  = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )
        pw_page = context.new_page()

        for page_num in range(1, max_pages + 1):
            url = f"{IT_URL}&gp={page_num}"
            print(f"  페이지 {page_num} 스크래핑 중... ({url})")

            html = get_html(pw_page, url)
            if html is None:
                print(f"  [!] 페이지 {page_num} 로드 실패, 중단")
                break

            contests, raw_count, has_next = parse_page(html, page_num)

            new = [c for c in contests if c["title"] not in seen_titles]
            seen_titles.update(c["title"] for c in new)
            all_contests.extend(new)

            print(f"  → 전체 {raw_count}개 중 {len(contests)}개 수집 (누적 {len(all_contests)}개)")

            if raw_count == 0 or not has_next:
                break

            time.sleep(1.5)

        browser.close()

    return all_contests


def save(contests: list, path: str = "data/contests.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total":        len(contests),
        "contests":     contests,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장 완료 → {path}  (총 {len(contests)}개)")


if __name__ == "__main__":
    print("위비티 IT 공모전 스크래핑 시작...")
    contests = scrape_all(max_pages=70)
    save(contests)
    print("완료!")
