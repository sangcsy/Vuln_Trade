# AGENT.md

## Project

- `Vuln Trade`
- Flask + Jinja2 + MySQL + Nginx + Docker Compose
- 금융형 UI를 가진 의도적 취약점 실습 앱

## Keep In Mind

- 이 프로젝트는 기본적으로 `취약 버전`이다.
- 앱을 망가뜨리지 않는 선에서 의도적 취약점은 남겨둔다.
- 다만 사용자가 요청한 일부 영역은 이미 하드닝되었다.

## Current State

- 실시간 시세는 `stocks.current_price` + `stock_price_history`로 관리
- 상세 차트는 `10초 / 30초 / 1분 / 10분 / 1시간` 보기 지원
- 홈/포트폴리오/상세 차트는 시간 기반 툴팁 사용
- 커뮤니티는 게시글 조회 가능, 수정은 본인만 가능
- 관리자 페이지는 `/auth/admin-login`을 통한 관리자 인증 필요

## First Files To Read

- `app/src/routes/main.py`
- `app/src/routes/stocks.py`
- `app/src/routes/community.py`
- `app/src/routes/auth.py`
- `app/src/db.py`
- `app/src/static/js/app.js`
- `app/src/static/css/style.css`
- `scheduler/update_prices.py`

## Important Notes

- `app/src/db.py`에서 런타임 보정과 시세 히스토리 백필을 한다.
- `scheduler/update_prices.py`는 종목별 최근 히스토리를 유지한다.
- 관리자 비밀번호 해시는 런타임에서 보정된다.
- 템플릿/JS 수정 후 브라우저 캐시 때문에 오동작처럼 보일 수 있다.

## Run

```powershell
docker compose up --build
docker compose restart app web scheduler
```

DB 초기화가 필요하면:

```powershell
docker compose down -v
docker compose up --build
```

## Working Style

- 새로 만들기보다 현재 구조를 읽고 이어서 수정할 것
- 보안 취약점을 자동으로 전부 제거하지 말 것
- 사용자가 특정 부분만 막아달라고 하면 그 부분만 좁게 수정할 것
