# Marketing Dashboard - Architecture & Developer Documentation

> 프로젝트 전체 개요는 [**README.md**](README.md)를, 개발 여정 기록은 [**DEVELOPMENT_HISTORY.md**](DEVELOPMENT_HISTORY.md)를 참고하세요.

This document provides a deep-dive into the project's internal architecture, modules, and workflows. For a general overview, setup, and deployment instructions, please refer to the main [README.md](README.md) file.

---

## Table of Contents

1.  [**Architecture Overview**](#1-architecture-overview)
2.  [**Backend Module Reference (Expandable)**](#2-backend-module-reference-expandable)
3.  [**Frontend Module Reference (Expandable)**](#3-frontend-module-reference-expandable)
4.  [**Detailed Workflow Analysis (Expandable)**](#4-detailed-workflow-analysis-expandable)

---

## 1. Architecture Overview

The application follows a decoupled architecture with a Python Flask backend serving as a RESTful API and a vanilla JavaScript single-page application (SPA) as the frontend.

-   **Frontend (Client-Side):** Renders the UI, handles user interactions, and makes API requests. It uses **Chart.js** for data visualization.
-   **Backend (Server-Side):** Serves the application, provides API endpoints for data and PDF generation, and handles authentication logic.
-   **External Services:** Leverages **WordPress** for user authentication and cover image hosting, **Google Analytics 4** for web metrics, **SERanking** for SEO data, and **OpenAI** for AI-powered summaries.

---

## 2. Backend Module Reference (Expandable)

<details>
<summary><code>app.py</code> - Main application entry point and route definitions.</summary>

-   **Purpose**: Sets up the Flask application, defines all API routes, and orchestrates data fetching from various services (Google Analytics, SE Ranking, WordPress) to render the marketing dashboard and generate PDF reports.
-   **Dependencies**: `app_factory`, `config`, `auth_service`, `ga4_service`, `seranking_service`, `pdf_generator`, `wp_auth`, `utils`, `flask`, `flask_jwt_extended`.
-   **Key Functions**:
    -   `index()`: Handles the main dashboard route (including the `?view=readme` logic), authentication, and rendering.
    -   `refresh()`: Refreshes JWT access tokens.
    -   `logout()`: Handles user logout and JWT blacklisting.
    -   `/api/*`: A collection of routes that provide data (GA4, SERanking), AI summaries, and PDF generation services to the frontend.

</details>

<details>
<summary><code>app_factory.py</code> - Flask application factory.</summary>

-   **Purpose**: Implements the factory pattern for creating the Flask application instance. This allows for flexible application setup, especially for testing and managing different environments. It also sets up JWT management, the token blacklist database, and logging.
-   **Dependencies**: `flask`, `flask_cors`, `flask_jwt_extended`, `flask_limiter`, `config`.
-   **Key Functions**:
    -   `create_app()`: The main factory function that returns a configured Flask app instance. It initializes all Flask extensions and defines JWT error handlers.

</details>

<details>
<summary><code>auth_service.py</code> - Google Analytics authentication service.</summary>

-   **Purpose**: Manages the OAuth 2.0 credentials required to access the Google Analytics Data API (GA4). It handles loading existing credentials, refreshing them when expired, and initiating the OAuth flow to create new ones if necessary.
-   **Dependencies**: `google.oauth2.credentials`, `google_auth_oauthlib.flow`, `config`.
-   **Key Functions**:
    -   `get_google_analytics_credentials()`: Orchestrates the entire credential management process, ensuring valid credentials are always available for the application.

</details>

<details>
<summary><code>config.py</code> - Centralized configuration management.</summary>

-   **Purpose**: Centralizes all configuration settings. It loads environment variables from a `.env` file and defines parameters for Google Analytics, SERanking, WordPress, Flask environment, and PDF font management.
-   **Dependencies**: `os`, `pathlib`, `dotenv`.
-   **Key Functions**:
    -   `validate_fonts()`: Verifies the existence of all configured font files at startup.

</details>

<details>
<summary><code>ga4_service.py</code> - Google Analytics 4 data service.</summary>

-   **Purpose**: Interacts with the GA4 Data API to fetch web analytics metrics. It processes the raw API responses into a structured format and calculates comparative data for different time periods.
-   **Dependencies**: `google.analytics.data_v1beta`, `auth_service`.
-   **Key Functions**:
    -   `get_ga4_data_internal()`: Fetches and processes GA4 data for a specified property and date range, returning a comprehensive dictionary of metrics.

</details>

<details>
<summary><code>passenger_wsgi.py</code> - WSGI entry point for Phusion Passenger.</summary>

-   **Purpose**: Serves as the entry point for the Flask application when deployed in a production cPanel environment using Phusion Passenger.
-   **Key Aspects**:
    -   **Thread Limiting**: Sets environment variables (`OPENBLAS_NUM_THREADS`, etc.) to `1` to prevent libraries like NumPy from overwhelming the server's CPU resources in a shared hosting environment.
    -   **Production Mode**: Explicitly sets `FLASK_ENV` to `production`.
    -   **Application Export**: Imports the Flask `app` object and renames it to `application`, the default variable name Phusion Passenger looks for.

</details>

<details>
<summary><code>pdf_generator.py</code> - PDF generation service.</summary>

-   **Purpose**: Encapsulates all logic related to generating PDF reports. It handles HTML to PDF conversion, dynamic creation of cover images with text overlays (using Pillow), and generation of chart images from data (using Matplotlib).
-   **Dependencies**: `xhtml2pdf`, `reportlab`, `PIL` (Pillow), `matplotlib`.
-   **Key Functions**:
    -   `generate_cover_image_base64()`: Generates the front cover image with dynamic text.
    -   `create_chart_image_base64()`: Generates various chart images and returns them as Base64 strings.
    -   `generate_pdf_from_html()`: The main function to convert a fully rendered HTML string into a PDF byte stream.

</details>

<details>
<summary><code>seranking_service.py</code> - SERanking data service.</summary>

-   **Purpose**: Fetches keyword ranking data and client site information from the SERanking API. It processes the raw API responses into a structured format.
-   **Dependencies**: `requests`, `config`.
-   **Key Functions**:
    -   `get_seranking_data_internal()`: Retrieves detailed keyword ranking data for a specific site and date range.
    -   `get_clients_for_frontend()`: Prepares and returns a list of clients for the frontend dropdown.

</details>

<details>
<summary><code>utils.py</code> - General utility functions.</summary>

-   **Purpose**: Provides a collection of general-purpose helper functions used across the backend.
-   **Dependencies**: `base64`, `requests`.
-   **Key Functions**:
    -   `get_image_base64_from_url()`: Fetches an image from a URL and returns its Base64 encoded string.
    -   `get_cover_images_from_wp()`: Fetches image URLs from a specified WordPress media category.

</details>

<details>
<summary><code>wp_auth.py</code> - WordPress authentication verification service.</summary>

-   **Purpose**: Provides the `AuthManager` class, which is responsible for verifying authentication requests originating from the external WordPress site. It validates parameters and JWTs to ensure secure access.
-   **Dependencies**: `hmac`, `hashlib`, `flask`.
-   **Key Classes**:
    -   `AuthManager`: The core class that handles the verification logic.

</details>

---

## 3. Frontend Module Reference (Expandable)

<details>
<summary><code>templates/index.html</code> - Main dashboard HTML template.</summary>

-   **Purpose**: Defines the structure and layout of the single-page application. It includes placeholders for all dynamic data and loads all necessary JavaScript modules.

</details>

<details>
<summary><code>templates/report_full_document.html</code> - PDF report HTML template.</summary>

-   **Purpose**: Defines the structure, content, and styling for the multi-page PDF reports. It is rendered by the backend with Jinja2, injecting all dynamic data before being converted to PDF. It includes `@page` CSS rules for PDF-specific layout.

</details>

<details>
<summary><code>static/js/main.js</code> - Main frontend application orchestrator.</summary>

-   **Purpose**: The entry point for all frontend logic. It initializes the UI, handles user events (e.g., button clicks), and orchestrates calls to other services for data fetching, chart rendering, and PDF generation.

</details>

<details>
<summary><code>static/js/apiService.js</code> - Backend API communication service.</summary>

-   **Purpose**: Centralizes all `fetch` requests to the backend API. Provides a clean interface for other frontend modules to request data without needing to know the specific endpoint URLs.

</details>

<details>
<summary><code>static/js/chartService.js</code> - Chart management service.</summary>

-   **Purpose**: Manages the creation, updating, and destruction of all charts on the dashboard using the **Chart.js** library.

</details>

<details>
<summary><code>static/js/jwt-manager.js</code> - JWT session management service.</summary>

-   **Purpose**: A critical module for session handling. It automatically refreshes JWTs before they expire, intercepts all API calls to attach the current token, and handles 401 (Unauthorized) errors by attempting a token refresh.

</details>

<details>
<summary><code>static/js/session-guard.js</code> - Session expiration UI service.</summary>

-   **Purpose**: Monitors the JWT expiration time and provides UI notifications (toasts, modals) to the user, warning them of an impending or expired session and guiding them to re-authenticate.

</details>

<details>
<summary>Other Frontend Services</summary>

-   `domElements.js`: Centralizes references to all DOM elements.
-   `ga4DisplayService.js`: Renders GA4-specific data into the UI.
-   `serankingDisplayService.js`: Renders SERanking tables and lists into the UI.
-   `pdfService.js`: Handles the client-side logic for requesting and receiving PDF files from the backend.
-   `uiService.js`: Manages general UI state like loading spinners and messages.
-   `utils.js`: Contains frontend helper functions.

</details>

---

## 4. Detailed Workflow Analysis (Expandable)

<details>
<summary><strong>User Authentication Workflow</strong></summary>

1.  **Initial Access**: User visits the dashboard. If no valid JWT is found, `app.py` redirects them to the WordPress login page.
2.  **WordPress Login**: User logs in on WordPress, which redirects back with authentication parameters in the request.
3.  **JWT Issuance**: The `wp_auth.py` module verifies the request. If valid, `app.py` issues its own access/refresh JWTs and sets them as secure, HTTP-only cookies.
4.  **Session Management**: The frontend `jwt-manager.js` handles the automatic attachment of tokens to API calls and silent token refreshing in the background. `session-guard.js` monitors expiration to warn the user.
5.  **Logout**: The frontend calls `/api/logout`. The backend blacklists the JWT in the `instance/data/blacklist.db` and clears the browser cookies.

</details>

<details>
<summary><strong>Data Loading & Display Workflow</strong></summary>

1.  **User Interaction**: User selects a client and date range and clicks "Load Data".
2.  **API Calls**: `main.js` triggers `apiService.js` to make parallel `fetch` requests to the backend's `/api/ga4_data` and `/api/seranking_data` endpoints.
3.  **Backend Processing**: `app.py` routes the requests to the appropriate service modules (`ga4_service.py`, `seranking_service.py`). These modules fetch data from the external APIs, process and structure the data, and return clean JSON.
4.  **UI Update**: `main.js` receives the JSON data. It passes the data to `ga4DisplayService.js` and `serankingDisplayService.js` to populate the UI elements, and to `chartService.js` to render the visual charts.

</details>

<details>
<summary><strong>PDF Report Generation Workflow</strong></summary>

1.  **User Interaction**: User clicks the "Generate PDF Report" button.
2.  **Request to Backend**: `pdfService.js` sends a POST request to `/generate-pdf-report` containing all the necessary data (client info, GA4/SERanking data, selected cover image URLs).
3.  **PDF Creation**: The `pdf_generator.py` module on the backend takes over.
    -   It renders the `report_full_document.html` template with all the data.
    -   It generates chart images on-the-fly using Matplotlib.
    -   It creates dynamic cover pages using Pillow.
    -   It converts the final, rich HTML into a PDF using `xhtml2pdf`.
4.  **Download**: The generated PDF is streamed back to the browser, where `pdfService.js` prompts the user to download it.

</details>

---
---

# 마케팅 대시보드 - 아키텍처 및 개발자 문서 (한국어)

> 프로젝트 전체 개요는 [**README.md**](README.md)를, 개발 과정의 기술적 여정은 [**DEVELOPMENT_HISTORY.md**](DEVELOPMENT_HISTORY.md)를 참고하세요.

이 문서는 프로젝트의 내부 아키텍처, 모듈 구성, 그리고 주요 워크플로우를 상세히 설명합니다. 일반적인 개요, 설정 및 배포 방법은 [README.md](README.md)를 참고하세요.

---

## 목차

1.  [**아키텍처 개요**](#1-아키텍처-개요)
2.  [**백엔드 모듈 레퍼런스 (펼쳐보기)**](#2-백엔드-모듈-레퍼런스-펼쳐보기)
3.  [**프론트엔드 모듈 레퍼런스 (펼쳐보기)**](#3-프론트엔드-모듈-레퍼런스-펼쳐보기)
4.  [**상세 워크플로우 분석 (펼쳐보기)**](#4-상세-워크플로우-분석-펼쳐보기)

---

## 1. 아키텍처 개요

본 애플리케이션은 **디커플드(Decoupled) 아키텍처**를 채택합니다. Python Flask 백엔드가 RESTful API 서버 역할을 담당하고, 바닐라 JavaScript로 구현된 단일 페이지 애플리케이션(SPA)이 프론트엔드를 구성합니다.

-   **프론트엔드 (클라이언트):** UI 렌더링, 사용자 인터랙션 처리, API 요청 담당. **Chart.js**를 활용한 데이터 시각화.
-   **백엔드 (서버):** 애플리케이션 서빙, 데이터 및 PDF 생성용 API 엔드포인트 제공, 인증 로직 처리.
-   **외부 서비스:** 사용자 인증 및 커버 이미지 호스팅은 **WordPress**, 웹 지표는 **Google Analytics 4**, SEO 데이터는 **SERanking**, AI 요약 기능은 **OpenAI** 활용.

---

## 2. 백엔드 모듈 레퍼런스 (펼쳐보기)

<details>
<summary><code>app.py</code> - 메인 애플리케이션 진입점 및 라우트 정의</summary>

-   **역할**: Flask 애플리케이션을 설정하고, 모든 API 라우트를 정의하며, 마케팅 대시보드 렌더링과 PDF 리포트 생성을 위해 각 서비스 모듈(Google Analytics, SERanking, WordPress)로의 데이터 요청을 조율합니다.
-   **의존성**: `app_factory`, `config`, `auth_service`, `ga4_service`, `seranking_service`, `pdf_generator`, `wp_auth`, `utils`, `flask`, `flask_jwt_extended`
-   **주요 함수**:
    -   `index()`: 메인 대시보드 라우트 처리 (`?view=readme` 로직 포함), 인증 및 렌더링.
    -   `refresh()`: JWT 액세스 토큰 갱신.
    -   `logout()`: 사용자 로그아웃 및 JWT 블랙리스트 처리.
    -   `/api/*`: GA4, SERanking 데이터, AI 요약, PDF 생성 서비스를 프론트엔드에 제공하는 API 라우트 모음.

</details>

<details>
<summary><code>app_factory.py</code> - Flask 애플리케이션 팩토리</summary>

-   **역할**: Flask 앱 인스턴스 생성을 위한 팩토리 패턴을 구현합니다. 테스트 및 다양한 환경 관리를 위한 유연한 앱 설정이 가능하며, JWT 관리, 토큰 블랙리스트 DB, 로깅을 초기화합니다.
-   **의존성**: `flask`, `flask_cors`, `flask_jwt_extended`, `flask_limiter`, `config`
-   **주요 함수**:
    -   `create_app()`: 설정이 완료된 Flask 앱 인스턴스를 반환하는 메인 팩토리 함수. 모든 Flask 확장 모듈 초기화 및 JWT 에러 핸들러 정의.

</details>

<details>
<summary><code>auth_service.py</code> - Google Analytics 인증 서비스</summary>

-   **역할**: Google Analytics Data API(GA4) 접근에 필요한 OAuth 2.0 크리덴셜을 관리합니다. 기존 크리덴셜 로딩, 만료 시 갱신, 신규 크리덴셜 생성을 위한 OAuth 플로우 시작을 처리합니다.
-   **의존성**: `google.oauth2.credentials`, `google_auth_oauthlib.flow`, `config`
-   **주요 함수**:
    -   `get_google_analytics_credentials()`: 전체 크리덴셜 관리 프로세스를 조율하여 애플리케이션에 항상 유효한 크리덴셜이 제공되도록 보장.

</details>

<details>
<summary><code>config.py</code> - 중앙 집중식 설정 관리</summary>

-   **역할**: 모든 설정을 중앙에서 관리합니다. `.env` 파일에서 환경 변수를 로드하고 Google Analytics, SERanking, WordPress, Flask 환경, PDF 폰트 관리 파라미터를 정의합니다.
-   **의존성**: `os`, `pathlib`, `dotenv`
-   **주요 함수**:
    -   `validate_fonts()`: 애플리케이션 시작 시 설정된 모든 폰트 파일의 존재 여부를 검증.

</details>

<details>
<summary><code>ga4_service.py</code> - Google Analytics 4 데이터 서비스</summary>

-   **역할**: GA4 Data API와 통신하여 웹 분석 지표를 가져옵니다. 원시 API 응답을 구조화된 형식으로 처리하고 기간별 비교 데이터를 계산합니다.
-   **의존성**: `google.analytics.data_v1beta`, `auth_service`
-   **주요 함수**:
    -   `get_ga4_data_internal()`: 지정된 속성(Property)과 날짜 범위에 대한 GA4 데이터를 가져와 처리하고, 종합적인 지표 딕셔너리를 반환.

</details>

<details>
<summary><code>passenger_wsgi.py</code> - Phusion Passenger WSGI 진입점</summary>

-   **역할**: cPanel 운영 환경에서 Phusion Passenger로 Flask 애플리케이션을 배포할 때의 진입점 역할을 합니다.
-   **핵심 사항**:
    -   **스레드 제한**: 공유 호스팅 환경에서 NumPy 등 라이브러리가 서버 CPU 리소스를 과점하는 것을 방지하기 위해 `OPENBLAS_NUM_THREADS` 등 환경 변수를 `1`로 설정.
    -   **프로덕션 모드**: `FLASK_ENV`를 명시적으로 `production`으로 설정.
    -   **애플리케이션 내보내기**: Flask `app` 객체를 임포트 후 Phusion Passenger가 찾는 기본 변수명인 `application`으로 재할당.

</details>

<details>
<summary><code>pdf_generator.py</code> - PDF 생성 서비스</summary>

-   **역할**: PDF 리포트 생성과 관련된 모든 로직을 캡슐화합니다. HTML→PDF 변환, Pillow를 이용한 텍스트 오버레이 커버 이미지 동적 생성, Matplotlib을 활용한 차트 이미지 생성을 담당합니다.
-   **의존성**: `xhtml2pdf`, `reportlab`, `PIL` (Pillow), `matplotlib`
-   **주요 함수**:
    -   `generate_cover_image_base64()`: 동적 텍스트가 삽입된 표지 이미지 생성.
    -   `create_chart_image_base64()`: 다양한 차트 이미지를 생성하고 Base64 문자열로 반환.
    -   `generate_pdf_from_html()`: 완전히 렌더링된 HTML 문자열을 PDF 바이트 스트림으로 변환하는 메인 함수.

</details>

<details>
<summary><code>seranking_service.py</code> - SERanking 데이터 서비스</summary>

-   **역할**: SERanking API에서 키워드 순위 데이터와 클라이언트 사이트 정보를 가져옵니다. 원시 API 응답을 구조화된 형식으로 처리합니다.
-   **의존성**: `requests`, `config`
-   **주요 함수**:
    -   `get_seranking_data_internal()`: 특정 사이트와 날짜 범위에 대한 상세 키워드 순위 데이터 조회.
    -   `get_clients_for_frontend()`: 프론트엔드 드롭다운용 클라이언트 목록 준비 및 반환.

</details>

<details>
<summary><code>utils.py</code> - 공통 유틸리티 함수</summary>

-   **역할**: 백엔드 전반에 걸쳐 사용되는 범용 헬퍼 함수 모음을 제공합니다.
-   **의존성**: `base64`, `requests`
-   **주요 함수**:
    -   `get_image_base64_from_url()`: URL에서 이미지를 가져와 Base64 인코딩 문자열로 반환.
    -   `get_cover_images_from_wp()`: 지정된 WordPress 미디어 카테고리에서 이미지 URL 목록을 가져옴.

</details>

<details>
<summary><code>wp_auth.py</code> - WordPress 인증 검증 서비스</summary>

-   **역할**: 외부 WordPress 사이트로부터 들어오는 인증 요청을 검증하는 `AuthManager` 클래스를 제공합니다. 파라미터와 JWT를 검증하여 안전한 접근을 보장합니다.
-   **의존성**: `hmac`, `hashlib`, `flask`
-   **주요 클래스**:
    -   `AuthManager`: 검증 로직 전체를 처리하는 핵심 클래스.

</details>

---

## 3. 프론트엔드 모듈 레퍼런스 (펼쳐보기)

<details>
<summary><code>templates/index.html</code> - 메인 대시보드 HTML 템플릿</summary>

-   **역할**: 단일 페이지 애플리케이션(SPA)의 구조와 레이아웃을 정의합니다. 모든 동적 데이터를 위한 플레이스홀더가 포함되어 있으며, 필요한 모든 JavaScript 모듈을 로드합니다.

</details>

<details>
<summary><code>templates/report_full_document.html</code> - PDF 리포트 HTML 템플릿</summary>

-   **역할**: 다중 페이지 PDF 리포트의 구조, 내용, 스타일을 정의합니다. 백엔드에서 Jinja2로 렌더링되어 모든 동적 데이터가 주입된 후 PDF로 변환됩니다. PDF 전용 레이아웃을 위한 `@page` CSS 규칙이 포함되어 있습니다.

</details>

<details>
<summary><code>static/js/main.js</code> - 메인 프론트엔드 오케스트레이터</summary>

-   **역할**: 모든 프론트엔드 로직의 진입점입니다. UI 초기화, 사용자 이벤트(버튼 클릭 등) 처리, 데이터 페칭·차트 렌더링·PDF 생성을 위한 각 서비스 호출을 조율합니다.

</details>

<details>
<summary><code>static/js/apiService.js</code> - 백엔드 API 통신 서비스</summary>

-   **역할**: 백엔드 API에 대한 모든 `fetch` 요청을 중앙에서 관리합니다. 다른 프론트엔드 모듈이 엔드포인트 URL을 알 필요 없이 데이터를 요청할 수 있는 깔끔한 인터페이스를 제공합니다.

</details>

<details>
<summary><code>static/js/chartService.js</code> - 차트 관리 서비스</summary>

-   **역할**: **Chart.js** 라이브러리를 사용하여 대시보드의 모든 차트 생성, 업데이트, 삭제를 관리합니다.

</details>

<details>
<summary><code>static/js/jwt-manager.js</code> - JWT 세션 관리 서비스</summary>

-   **역할**: 세션 처리를 위한 핵심 모듈입니다. JWT 만료 전 자동 갱신, 모든 API 호출에 현재 토큰 자동 첨부, 401(Unauthorized) 에러 발생 시 토큰 갱신 시도를 처리합니다.

</details>

<details>
<summary><code>static/js/session-guard.js</code> - 세션 만료 UI 서비스</summary>

-   **역할**: JWT 만료 시각을 모니터링하고, 세션 만료가 임박하거나 만료되었을 때 사용자에게 UI 알림(토스트, 모달)을 제공하여 재인증을 안내합니다.

</details>

<details>
<summary>기타 프론트엔드 서비스</summary>

-   `domElements.js`: 모든 DOM 요소에 대한 참조를 중앙에서 관리.
-   `ga4DisplayService.js`: GA4 데이터를 UI에 렌더링.
-   `serankingDisplayService.js`: SERanking 테이블 및 목록을 UI에 렌더링.
-   `pdfService.js`: 백엔드에 PDF를 요청하고 수신하는 클라이언트 측 로직 처리.
-   `uiService.js`: 로딩 스피너, 메시지 등 일반적인 UI 상태 관리.
-   `utils.js`: 프론트엔드 헬퍼 함수 모음.

</details>

---

## 4. 상세 워크플로우 분석 (펼쳐보기)

<details>
<summary><strong>사용자 인증 워크플로우</strong></summary>

1.  **최초 접근**: 사용자가 대시보드에 접속합니다. 유효한 JWT가 없으면 `app.py`가 WordPress 로그인 페이지로 리다이렉트합니다.
2.  **WordPress 로그인**: 사용자가 WordPress에서 로그인하면, 인증 파라미터를 포함하여 대시보드로 리다이렉트됩니다.
3.  **JWT 발급**: `wp_auth.py` 모듈이 요청을 검증합니다. 유효하면 `app.py`가 자체 Access/Refresh JWT를 발급하고 보안 HttpOnly 쿠키에 저장합니다.
4.  **세션 관리**: 프론트엔드 `jwt-manager.js`가 모든 API 호출에 토큰을 자동 첨부하고 백그라운드에서 토큰을 자동 갱신합니다. `session-guard.js`가 만료를 모니터링하여 사용자에게 경고합니다.
5.  **로그아웃**: 프론트엔드가 `/api/logout`을 호출하면, 백엔드가 `instance/data/blacklist.db`에 JWT를 블랙리스트 처리하고 브라우저 쿠키를 삭제합니다.

</details>

<details>
<summary><strong>데이터 로딩 및 표시 워크플로우</strong></summary>

1.  **사용자 인터랙션**: 사용자가 클라이언트와 날짜 범위를 선택하고 "데이터 불러오기"를 클릭합니다.
2.  **API 호출**: `main.js`가 `apiService.js`를 통해 백엔드의 `/api/ga4_data`와 `/api/seranking_data` 엔드포인트로 병렬 `fetch` 요청을 보냅니다.
3.  **백엔드 처리**: `app.py`가 요청을 해당 서비스 모듈(`ga4_service.py`, `seranking_service.py`)로 라우팅합니다. 각 모듈은 외부 API에서 데이터를 가져와 처리·구조화하여 깔끔한 JSON으로 반환합니다.
4.  **UI 업데이트**: `main.js`가 JSON 데이터를 받아 `ga4DisplayService.js`와 `serankingDisplayService.js`에 전달하여 UI 요소를 채우고, `chartService.js`에 전달하여 시각적 차트를 렌더링합니다.

</details>

<details>
<summary><strong>PDF 리포트 생성 워크플로우</strong></summary>

1.  **사용자 인터랙션**: 사용자가 "PDF 리포트 생성" 버튼을 클릭합니다.
2.  **백엔드 요청**: `pdfService.js`가 `/generate-pdf-report`로 POST 요청을 보냅니다. 요청에는 클라이언트 정보, GA4/SERanking 데이터, 선택한 커버 이미지 URL 등 필요한 모든 데이터가 포함됩니다.
3.  **PDF 생성**: 백엔드의 `pdf_generator.py` 모듈이 처리를 시작합니다.
    -   `report_full_document.html` 템플릿을 모든 데이터와 함께 렌더링합니다.
    -   Matplotlib으로 차트 이미지를 즉석에서 생성합니다.
    -   Pillow로 동적 커버 페이지를 생성합니다.
    -   최종 완성된 HTML(+Base64 이미지)을 `xhtml2pdf`로 PDF 변환합니다.
4.  **다운로드**: 생성된 PDF가 브라우저로 스트리밍되고, `pdfService.js`가 사용자에게 다운로드를 안내합니다.

</details>