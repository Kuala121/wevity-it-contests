"""
위비티(wevity.com) IT 공모전 스크래퍼
웹/모바일/IT 카테고리(cidx=6)의 공모전을 수집하여 data/contests.json에 저장합니다.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime

BASE_URL = "https://www.wevity.com"
IT_URL = "https://www.wevity.com/?c=find&s=1&cidx=6"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": "https://www.wevity.com/",
}

STATUS_MAP = {
    "ing":    "접수중",
    "soon":   "마감임박",
    "future": "접수예정",
    "end":    "마감",
}

DDAY_SORT = {
    "ing":    0,
    "soon":   1,
    "future": 2,
    "end":    3,
}


def scrape_page(page: int) -> tuple[list, bool]:
    url = f"{IT_URL}&gp={page}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except requests.RequestException as e:
        print(f"  [!] 페이지 {page} 요청 실패: {e}")
        return [], False

    soup = BeautifulSoup(resp.text, "lxml")
    contests = []

    items = soup.select("div.ms-list ul.list li:not(.top)")
    for item in items:
        tit_div = item.select_one("div.tit")
        if not tit_div:
            continue

        link_tag = tit_div.select_one("a")
        if not link_tag:
            continue

        # 배지(SPECIAL, IDEA, NEW 등)
        stat_span = link_tag.select_one("span.stat")
        badge = stat_span.get_text(strip=True) if stat_span else ""

        # 제목 (배지 텍스트 제거)
        if stat_span:
            stat_span.extract()
        title = link_tag.get_text(strip=True)

        # 공모전 링크
        href = link_tag.get("href", "")
        full_link = (BASE_URL + href) if href.startswith("?") else href

        # 분야(카테고리)
        sub_tit = tit_div.select_one("div.sub-tit")
        categories = []
        if sub_tit:
            cat_text = sub_tit.get_text(strip=True)
            if "분야 :" in cat_text:
                raw = cat_text.split("분야 :")[-1].strip()
                categories = [c.strip() for c in raw.split(",") if c.strip()]

        # 주최사
        organ_div = item.select_one("div.organ")
        organization = organ_div.get_text(strip=True) if organ_div else ""

        # D-Day & 상태
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

        # 조회수
        read_div = item.select_one("div.read")
        views_str = read_div.get_text(strip=True) if read_div else "0"
        views_num = int(views_str.replace(",", "")) if re.fullmatch(r"[\d,]+", views_str) else 0

        # 웹/모바일/IT 분야가 포함된 공모전만 수집
        if "웹/모바일/IT" not in categories:
            continue

        contests.append({
            "title": title,
            "link": full_link,
            "badge": badge,
            "categories": categories,
            "organization": organization,
            "dday": dday,
            "dday_num": dday_num,
            "status": status,
            "status_class": status_class,
            "views": views_str,
            "views_num": views_num,
        })

    # 다음 페이지 존재 여부
    has_next = False
    navi = soup.select_one("div.list-navi")
    if navi:
        for a in navi.select("a"):
            if f"gp={page + 1}" in (a.get("href") or ""):
                has_next = True
                break

    return contests, has_next


def scrape_all(max_pages: int = 10) -> list:
    all_contests = []
    for page in range(1, max_pages + 1):
        print(f"  페이지 {page} 스크래핑 중...")
        contests, has_next = scrape_page(page)
        all_contests.extend(contests)
        print(f"  → {len(contests)}개 수집 (누적 {len(all_contests)}개)")
        if not contests or not has_next:
            break
        time.sleep(1.2)   # 서버 부하 방지
    return all_contests


def save(contests: list, path: str = "data/contests.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(contests),
        "contests": contests,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장 완료 → {path}  (총 {len(contests)}개)")


if __name__ == "__main__":
    print("위비티 IT 공모전 스크래핑 시작...")
    contests = scrape_all(max_pages=10)
    save(contests)
    print("완료!")
