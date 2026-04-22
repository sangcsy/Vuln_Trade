# Vulnerable Virtual Finance Platform

가상 금융 거래 플랫폼과 커뮤니티를 결합한 교육용 웹 애플리케이션이다. Docker Compose로 실행되며, 정상적인 거래/송금/게시판 흐름을 제공한다. 이 프로젝트는 보안 실습과 웹 취약점 진단 학습을 위한 의도적 취약 앱이다.

## 프로젝트 개요

- Flask + Jinja2 기반 서버 렌더링 웹앱
- Nginx reverse proxy
- MySQL 데이터 저장
- scheduler 컨테이너가 주기적으로 주가 갱신
- 가상 금융 거래, 송금, 커뮤니티, 관리자 기능 제공

## 서비스 기능 요약

- 회원가입, 로그인, 로그아웃, 마이페이지
- 종목 목록, 종목 상세, 매수/매도, 포트폴리오, 거래 내역
- 사용자 간 송금, 송금 내역
- 게시글/댓글/파일 업로드 및 다운로드
- 관리자 대시보드, 사용자 목록, 전체 거래 내역, 게시글 관리

## 실행 방법

1. 프로젝트 루트에서 `docker compose up --build`
2. 브라우저에서 `http://localhost:8080`

## 기본 계정 정보

- 관리자
  - username: `admin`
  - password: `admin123`
- 일반 사용자
  - username: `user1`
  - password: `user123`
  - username: `user2`
  - password: `user123`

## 주요 URL

- `/`
- `/auth/login`
- `/stocks`
- `/stocks/portfolio`
- `/wallet/transfer`
- `/community`
- `/admin`

## 컨테이너 구조 설명

- `web`: 외부 요청을 받는 Nginx
- `app`: Flask 애플리케이션
- `db`: MySQL
- `scheduler`: 주기적으로 주가를 갱신하는 Python 스크립트

## 주의

이 프로젝트는 교육용 의도적 취약 앱이다. 실서비스 환경에 배포하거나 운영 목적으로 사용하면 안 된다.
