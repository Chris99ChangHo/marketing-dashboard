# Marketing Dashboard & Automated Reporting System

> **수작업 보고서 20분 → 2분으로 단축** | Google Analytics 4 + SERanking + OpenAI 연동 마케팅 대시보드

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?style=flat&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)

---

## 📄 문서 네비게이션

| 문서 | 설명 |
|------|------|
| **README.md** (현재 문서) | 프로젝트 개요, 주요 기능, 기술 스택, 설정 방법 |
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | 백엔드/프론트엔드 모듈 레퍼런스 및 상세 워크플로우 분석 |
| [**DEVELOPMENT_HISTORY.md**](DEVELOPMENT_HISTORY.md) | 인프라 제약(SIGTERM) 극복 및 하이브리드 PDF 렌더링 파이프라인 구축기 |

---

## 🚀 프로젝트 개요 및 비즈니스 임팩트

수작업으로 진행되던 마케팅 보고서 작성 프로세스의 병목을 해결한 **통합 마케팅 대시보드 및 리포트 자동화** 솔루션입니다. 

기존에는 GA4 등 각 플랫폼에 개별 접속하여 수치를 일일이 복사하고 붙여넣는 방식으로 리포트 작성에 약 20분이 소요되었습니다. 본 시스템을 통해 **드롭다운에서 고객사를 선택하는 즉시 핵심 지표(GA4, SERanking)가 연동되어 대시보드에 시각화**되며, OpenAI 기반의 인사이트 요약 모듈을 거쳐 **단 2분 만에 픽셀 퍼펙트(Pixel-Perfect)한 브리핑용 PDF를 추출**할 수 있도록 업무 파이프라인을 혁신했습니다.

- 📉 **업무 효율 극대화**: 수동 데이터 기입에 의존하던 약 20분의 리포팅 과정을 시스템 기반의 2분 프로세스로 단축
- 📊 **데이터 통합 뷰**: 트래픽(GA4)과 키워드 순위(SERanking) API 실시간 호출 및 통합 시각화
- 🤖 **AI 인사이트**: AI 요약 기능을 통한 빠르고 정확한 데이터 해석 지원

---

## 🔑 핵심 기능

### 1. 실시간 마케팅 대시보드 및 데이터 파이프라인
- GA4 및 SERanking 연동: 핵심 지표 실시간 시각화 (Chart.js)
- **데이터 무결성 검수(QA)**: API 연동 시 발생하는 예외(Exception) 처리 및 에러 로깅을 통해 결측치(Missing Value) 방어 로직 적용
- 멀티 클라이언트 지원: 드롭다운 기반 다중 고객사 조회 및 `clients.json` 연동 아키텍처

### 2. PDF 리포팅 자동화
- 서버 사이드 차트 렌더링 (Matplotlib → Base64 → xhtml2pdf) 기반의 시스템 독립적 아키텍처 구축
- Pillow 기반 동적 커버 이미지 생성 및 WordPress 미디어 라이브러리 연동

### 3. 엔터프라이즈급 보안 아키텍처
- **JWT 이중 세션 (Access/Refresh Token)**: Flask-JWT-Extended 기반
- **XSS/CSRF 완벽 차단**: `HttpOnly` + `Secure` 쿠키, CSRF 토큰 분리 검증
- **WordPress 연동 인증**: 외부 WordPress 사용자 인증을 Flask 백엔드와 연동

---

## 🛠 기술 스택

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
