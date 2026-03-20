# IT 공모전 모음 🖥️

위비티(wevity.com)의 **웹/모바일/IT** 분야 공모전을 자동으로 수집해 보여주는 정적 웹사이트입니다.

🔗 **라이브 사이트** → `https://<your-username>.github.io/wevity-it-contests`

---

## 기능

- 위비티에서 IT 공모전 자동 스크래핑 (매일 자정 KST)
- 상태별 필터: 접수중 / 마감임박 / 접수예정 / 마감
- 제목·주최사 검색
- 정렬: 마감일순 / 조회수순 / 가나다순
- 원본 공모전 페이지 바로가기

---

## 로컬 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 스크래핑 실행

```bash
python scraper.py
```

`data/contests.json` 파일이 생성됩니다.

### 3. 웹 서버 실행

```bash
python -m http.server 8080
```

브라우저에서 `http://localhost:8080` 접속

---

## GitHub에 배포 (GitHub Pages)

### 1. 저장소 생성 후 Push

```bash
git remote add origin https://github.com/<username>/wevity-it-contests.git
git push -u origin main
```

### 2. GitHub Pages 설정

저장소 → **Settings** → **Pages** → Source: `Deploy from a branch` → Branch: `main` / `/ (root)` → Save

### 3. 자동 업데이트 활성화

저장소 → **Settings** → **Actions** → **General** → "Allow all actions" 선택 후 저장

이후 매일 자정(KST)에 자동으로 데이터가 업데이트됩니다.
**Actions** 탭에서 `Scrape & Deploy` 워크플로우를 수동으로 실행할 수도 있습니다.

---

## 파일 구조

```
wevity-it-contests/
├── index.html                  # 메인 웹페이지
├── scraper.py                  # 스크래퍼
├── requirements.txt
├── data/
│   └── contests.json           # 스크래핑된 데이터
└── .github/
    └── workflows/
        └── scrape.yml          # 자동 스크래핑 워크플로우
```

---

## 주의사항

- 과도한 요청은 서버에 부담을 줄 수 있으므로 스크래핑 간격을 유지합니다.
- 위비티의 HTML 구조가 변경되면 스크래퍼 수정이 필요할 수 있습니다.
- 데이터의 저작권은 위비티(wevity.com)에 있습니다.
