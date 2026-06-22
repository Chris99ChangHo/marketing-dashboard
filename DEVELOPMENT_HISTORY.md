# 🚀 Marketing Dashboard & PDF Automation: Robust Architecture on Restricted Infrastructure

> **"극한의 인프라 제약을 돌파한 하이브리드 렌더링 및 안정적인 자동화 파이프라인"**
>
> 본 프로젝트는 cPanel 공유 호스팅이라는 제한적인 서버 환경(OS 패키지 설치 불가, 스레드 제한 등)의 한계를 극복하고, 픽셀 퍼펙트(Pixel-Perfect)한 1-Click PDF 리포트 자동화를 구현하기 위해 설계된 견고한 백엔드 시스템 아키텍처입니다.

## 1. Project Overview (프로젝트 개요)

- **프로젝트 목적**: 수작업으로 약 20분 이상 소요되던 마케팅 보고서 작성 프로세스의 비효율을 해결하기 위해, 시스템 권한이 제한된 환경에서도 안정적으로 동작하는 데이터 시각화 및 PDF 자동화 구축.
- **기술 스택**:
  <br>
  <img src="[https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)"/>
  <img src="[https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)"/>
  <img src="[https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white](https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white)"/>
  <img src="[https://img.shields.io/badge/xhtml2pdf-E34F26?style=for-the-badge&logo=html5&logoColor=white](https://img.shields.io/badge/xhtml2pdf-E34F26?style=for-the-badge&logo=html5&logoColor=white)"/>
  <img src="[https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)"/>

단순한 API 데이터 호출을 넘어, 백엔드 서버 사이드 렌더링과 순수 파이썬(Pure Python) 기반의 PDF 변환 로직을 결합하여 외부 시스템 바이너리 의존성을 완벽하게 제거했습니다.

## 2. Architecture & Workflow (시스템 구조)

전체 PDF 자동화 파이프라인은 인프라 제약을 우회하기 위해 논리적으로 분리된 3단계 하이브리드 렌더링 모듈로 작동합니다.

- **Phase 1: 데이터 취합 및 인메모리 제어 (Data Fetching & Rate Limiting)**
  GA4 및 SERanking API를 통해 데이터를 호출합니다. 이때 Redis를 사용할 수 없는 호스팅 환경의 제약을 우회하기 위해, 단일 프로세스에 맞춘 인메모리 스토리지(`memory://`) 기반의 Rate Limiting을 적용하여 API 남용을 방어합니다.

- **Phase 2: 서버 사이드 차트 렌더링 (Server-Side Chart Rendering)**
  `xhtml2pdf`가 JavaScript(Chart.js)를 렌더링하지 못하는 한계를 극복하기 위해, 백엔드에서 `Matplotlib`을 활용해 데이터를 분석하고 차트 이미지를 생성한 뒤, 이를 Base64 문자열로 변환합니다.

- **Phase 3: 하이브리드 PDF 변환 (Hybrid PDF Generation)**
  생성된 Base64 차트 이미지와 OpenAI 기반 인사이트 요약 텍스트를 서버 사이드 템플릿(Jinja2)의 HTML에 주입하고, 시스템 의존성 없는 `xhtml2pdf`를 통해 픽셀 퍼펙트한 최종 PDF 파일로 추출해 냅니다.

## 3. Critical Troubleshooting & Core Logic (핵심 문제 해결 및 코드)

극한의 호스팅 인프라 제약 속에서 마주한 크리티컬 이슈와 이를 해결한 핵심 엔지니어링 접근법입니다.

### A. 시스템 바이너리 제약 극복: 하이브리드 PDF 렌더링 설계

PDF 자동화 구현 초기, Playwright(헤드리스 브라우저), WeasyPrint, PDFKit 등 최신 렌더링 라이브러리 도입을 5차례 시도했으나, cPanel 공유 호스팅의 엄격한 OS 패키지(C 라이브러리, 커스텀 바이너리) 설치 제한에 부딪혀 모두 실패했습니다.
이를 극복하기 위해, 시스템 권한이 필요 없는 순수 파이썬 라이브러리(`xhtml2pdf`)와 `Matplotlib`을 결합한 **하이브리드 렌더링 방식**을 고안하여 환경의 물리적 한계를 완벽히 우회했습니다.

```python
# [하이브리드 렌더링 Base64 주입 로직 예시 발췌]

def create_chart_image_base64(data):
    """
    JS 실행이 불가능한 PDF 변환 환경을 극복하기 위해
    백엔드에서 Matplotlib으로 차트를 생성하고 Base64로 인코딩하여 반환
    """
    import matplotlib.pyplot as plt
    import io, base64

    plt.figure(figsize=(8, 4))
    plt.plot(data['dates'], data['sessions'])
    # ... 차트 스타일링 생략 ...
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    plt.close()
    
    return base64.b64encode(img_buffer.getvalue()).decode('utf-8')
