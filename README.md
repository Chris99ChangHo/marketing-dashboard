# Marketing Dashboard & Automated Reporting System

> **수작업 보고서 30분 → 1-Click 자동화** | Google Analytics 4 + SERanking + OpenAI 연동 마케팅 대시보드

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?style=flat&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)

---

## 📄 문서 네비게이션

| 문서 | 설명 |
|------|------|
| **README.md** (현재 문서) | 프로젝트 개요, 주요 기능, 기술 스택, 설정 방법 |
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | 백엔드/프론트엔드 모듈 레퍼런스 및 상세 워크플로우 분석 |
| [**DEVELOPMENT_HISTORY.md**](DEVELOPMENT_HISTORY.md) | 개발 과정에서 마주한 기술적 난관과 해결 여정 (5전 6기의 PDF 자동화 등) |

---

## 🚀 프로젝트 개요 및 비즈니스 임팩트

수작업으로 진행되던 마케팅 보고서 작성 프로세스를 혁신적으로 단축한 **마케팅 대시보드 및 1-Click PDF 리포트 자동화** 솔루션입니다. Google Analytics 4 (GA4)와 SERanking API를 연동하여 핵심 지표를 대시보드 형태로 제공하며, 버튼 한 번으로 픽셀 퍼펙트(Pixel-Perfect)한 브리핑용 PDF를 추출합니다.

- 📉 **업무 효율 극대화**: 클라이언트별 보고서 작성에 소요되던 **약 30분의 수작업을 1-Click으로 단축**
- 📊 **데이터 통합 대시보드**: 트래픽(GA4)과 키워드 순위(SERanking)를 하나의 직관적인 뷰로 통합
- 🤖 **AI 인사이트**: OpenAI API를 활용한 데이터 요약으로 마케터-클라이언트 커뮤니케이션 비용 절감

---

## 🔑 핵심 기능

### 1. 실시간 마케팅 대시보드
- GA4 연동: 세션, 사용자, 이탈률, 전환율 등 핵심 지표 실시간 시각화 (Chart.js)
- SERanking 연동: 키워드별 검색 순위 추이 및 변동 현황
- 멀티 클라이언트 지원: `clients.json` 기반 다중 고객사 전환

### 2. 1-Click PDF 자동화
- 서버 사이드 차트 렌더링 (Matplotlib → Base64 → xhtml2pdf)
- Pillow 기반 동적 커버 이미지 생성
- WordPress 미디어 라이브러리에서 커버 이미지 자동 연동

### 3. 엔터프라이즈급 보안 아키텍처
- **JWT 이중 세션 (Access/Refresh Token)**: Flask-JWT-Extended 기반
- **XSS/CSRF 완벽 차단**: `HttpOnly` + `Secure` 쿠키, CSRF 토큰 분리 검증
- **WordPress 연동 인증**: 외부 WordPress 사용자 인증을 Flask 백엔드와 연동

---

## 🛠 Tech Stack

| 영역 | 기술 |
|------|------|
| **Backend** | Python 3.12, Flask, Flask-JWT-Extended, Flask-Limiter |
| **Frontend** | Vanilla JavaScript (ES Modules), HTML5/CSS3, Chart.js |
| **PDF 생성** | xhtml2pdf, Pillow, Matplotlib (서버 사이드 렌더링) |
| **API 연동** | Google Analytics Data API v1, SERanking API, OpenAI API |
| **인증** | WordPress OAuth 연동, JWT (HS256), HttpOnly Cookie |
| **배포** | cPanel Shared Hosting, Phusion Passenger (WSGI) |

---

## 🔒 보안 아키텍처

본 시스템은 외부 WordPress 인프라의 사용자 인증 정보를 활용하여 독립된 Flask 백엔드와 연동하는 구조입니다.

- **JWT 기반 이중 보안 세션**: WordPress 인증 파라미터 검증 후 Access/Refresh Token 이중 발급
- **XSS 및 CSRF 완벽 차단**: JavaScript 접근 불가 `HttpOnly`/`Secure` 쿠키 + CSRF 토큰 분리 검증
- **프론트엔드 Session Guard**: 토큰 만료 실시간 모니터링 → 자동 Refresh 또는 안전한 리다이렉트

---

## 📈 향후 확장성

- **Multi-Tenancy 아키텍처**: `clients.json` → DB 기반 레지스트리로 확장하여 N개 고객사를 단일 인스턴스에서 관리
- **B2B SaaS 형태**로의 발전 목표: 고객사별 GA4 Property ID / SERanking Site ID 1:N 매칭

---

## 📂 디렉토리 구조

```text
.
├── app.py                 # 메인 Flask 라우터 및 API 엔드포인트
├── app_factory.py         # Flask 앱 팩토리, JWT 및 설정 초기화
├── config.py              # 중앙 집중식 설정 관리
├── ga4_service.py         # Google Analytics 4 연동 및 데이터 처리
├── seranking_service.py   # SERanking API 연동
├── pdf_generator.py       # xhtml2pdf + Matplotlib 기반 PDF 생성 엔진
├── auth_service.py        # Google OAuth 2.0 크리덴셜 관리
├── wp_auth.py             # WordPress 연동 JWT 검증 및 로그인 처리
├── utils.py               # 공통 유틸리티 함수
├── passenger_wsgi.py      # Phusion Passenger (cPanel) WSGI 진입점
├── requirements.txt       # Python 패키지 의존성
├── .env.example           # 환경변수 설정 예시 (실제 .env는 .gitignore 처리)
├── client_secret.example.json  # Google OAuth 설정 예시
├── instance/
│   └── clients.example.json    # 멀티 클라이언트 설정 예시
├── static/                # CSS, JS (API Fetch, Session Guard, Chart UI 등)
└── templates/             # Jinja2 HTML 템플릿 (대시보드 UI, PDF 레이아웃)
```

---

## ⚙️ 설정 방법 (Local Setup)

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 실제 API 키와 설정값 입력
```

필요한 환경변수:

| 변수명 | 설명 |
|--------|------|
| `SERANKING_API_KEY` | SERanking API 키 |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `FLASK_SECRET_KEY` | Flask 세션 비밀 키 |
| `WORDPRESS_AUTH_URL` | WordPress 로그인 URL |
| `WP_API_USERNAME` | WordPress API 사용자명 |
| `WP_API_APPLICATION_PASSWORD` | WordPress 앱 비밀번호 |
| `GA4_MULTI_TENANT` | 멀티 테넌트 모드 활성화 (`true`/`false`) |

### 3. Google Analytics 설정
- `client_secret.example.json`을 참고하여 `client_secret.json` 작성
- Google Cloud Console에서 Analytics Data API 활성화 및 OAuth 2.0 클라이언트 생성

### 4. 클라이언트 설정
- `instance/clients.example.json`을 참고하여 `instance/clients.json` 작성

### 5. 실행
```bash
python app.py
```

---

## 📖 개발 여정

> **cPanel 공유 호스팅**이라는 극한의 인프라 제약 속에서 PDF 자동화를 구현하기까지 5번의 실패와 1번의 성공.  
> SIGTERM 프로세스 킬링, Redis 없는 Rate Limiting 등 실전 트러블슈팅 경험을 담았습니다.

👉 [**DEVELOPMENT_HISTORY.md**](DEVELOPMENT_HISTORY.md)에서 전체 개발 여정을 확인하세요.

---

## 📐 아키텍처 상세

> 각 모듈의 역할, 의존성, 핵심 함수 및 인증·데이터 로딩·PDF 생성 워크플로우 전체를 다룹니다.

👉 [**ARCHITECTURE.md**](ARCHITECTURE.md)에서 상세 아키텍처를 확인하세요.