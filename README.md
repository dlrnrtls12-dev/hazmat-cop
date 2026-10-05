# 🛡️ Hazmat Cop (위험물 기획단속 스마트 현장도우미)

> **소방특별사법경찰 실무를 위한 위험물안전관리법 & 경기도 조례 통합 현장 단속 지원 시스템**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python)](https://python.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 개요

**Hazmat Cop**은 소방특별사법경찰관(특사경)이 위험물 제조·저장·취급 현장에서 마주하는 복잡한 법적 판단, 배수 계산, 현장 채증, 조서 및 확인서 작성을 모바일 및 태블릿 환경에서 신속·정확하게 수행할 수 있도록 지원하는 올인원 웹 애플리케이션입니다.

---

## 🚀 현장 실무 5대 핵심 기능

### 1. 지정수량 배수 계산 & 종합 위법 판정
- **용기 규격 프리셋 & 중첩 계산**: 200L 드럼, 20L 말통, 18L 캔, 1,000L IBC, 55gal 드럼, 1gal 캔 등 다양한 규격 지원 및 동일 물질 다수 규격 보관 시 행별 자동 집계.
- **수량 및 장소 교차 판단**:
  - `1.0배 이상 (무허가 장소)`: 위험물안전관리법 제5조제1항 위반 (3년 이하 징역 또는 3천만원 이하 벌금, **형사입건**)
  - `0.2배 이상 ~ 1.0배 미만`: 경기도 조례 제5조/제6조 소량위험물 기준 위반 (**행정 시정명령**)
  - `운반용기 기준 위반 (법 제20조)`: 지정수량 미만이라도 전국 공통 적용 (**200만원 이하 과태료**)
  - `출입·검사 거부/기피 (법 제27조제6항)`: 즉시 경고 및 형사처벌 규정 안내

### 2. 현장 채증 사진 GPS·시간 워터마크 Burn-in & 모바일 전자서명 A4 PDF
- **실시간 워터마크 영구 각인**: 모바일 카메라 촬영 즉시 HTML5 Canvas를 이용해 촬영 일시(`YYYY-MM-DD HH:mm:ss`), 현장 GPS 좌표(`37.xxxxx°N, 126.xxxxx°E`), 단속관 성명, 채증 카테고리를 사진 자체에 번인(Burn-in) 합성.
- **피의자 & 단속관 듀얼 터치 서명**: 화면 상에서 손가락 또는 스타일러스 펜으로 자필 서명 및 직인 날인.
- **공식 소방특사경 A4 PDF 패키징**: `html2pdf.js` 기반으로 공문서 규격의 [위반사실확인서], [시료채취확인서], [범죄인지보고서]를 별첨 채증 사진(2열 그리드)과 함께 단일 PDF로 원터치 다운로드.

### 3. 통신 음영 지역 대비 로컬 오프라인 모드 (Offline-First)
- 지하탱크실, 두꺼운 샌드위치 패널 공장 등 LTE/5G 신호가 잡히지 않는 통신 음영 지역에서도 브라우저 내장 자바스크립트 엔진(`calculateLocally`)이 자동 가동.
- 인터넷 단절 상태에서도 배수 계산, 위법성 판단, 워터마크 사진 보관, PDF 생성이 100% 정상 작동.

### 4. 무표시 미상물질 감별기 (MSDS 역산 & 간이 문답 & 시료 채취)
- **MSDS 인화점(℃) 역산기**: 현장에서 확보한 MSDS나 성적서 상의 인화점(℃) 및 수용성 여부를 입력하면 제1~4석유류 품명 및 법정지정수량을 자동 판정.
- **3단계 간이 문답 트리**: 라벨이 전혀 없는 무표시 말통의 경우 취기(신나/기름), 용도(세척/도장/연료), 수용성 여부 문답을 거쳐 단속 실무 원칙에 따라 제1석유류 비수용성(200L)으로 우선 가적용.
- **시료채취 봉인번호 자동 발급**: `GG-2026-SEAL-XXX` 형식의 봉인 번호 자동 채번 및 국립소방연구원 정밀 감정 의뢰 연계.

### 5. 단속관 안전 및 방폭 프로토콜 배너
- **가연성 유증기 폭발 하한계 체류 경보 (CRITICAL)**: 신나, 톨루엔 등 제1석유류 적발 시 비방폭 플래시/스위치 조작 엄금, 창문·출입문 개방 자연환기 수칙 안내.
- **금수성 물질 물 주수 절대 금지 경보 (CRITICAL)**: 제3류 위험물 적발 시 옥내소화전 등 수계 방수 엄금, D급 소화기 및 건조사 확보 안내.
- **필수 착용 PPE 체크리스트**: 갈색 정화통 방독마스크, 정전기 방지 안전화, 방폭 손전등 등 맞춤형 개인보호장구 가이드 제공.

---

## 🏛️ 추가 연동 모듈

- **대상처 공공데이터 스크리닝**: 경기도 31개 시·군 6,170개 등록 유해화학물질 취급사업장 실시간 검증.
- **국가법령 및 연혁(eflaw) 조회**: 법제처 및 소방청 유권해석례 전문(질의요지, 회답, 이유) 검색 및 특정 인허가일자 기준 시행 법령·부칙 경과조치 자동 매칭.
- **품명 & 안전수칙 백과**: 제1류~제6류 전체 품목 수 및 류별 통계, 물질별 소화 방법, 혼재 금지 기준 수록.
- **AI 법률 상담 챗봇**: 위험물안전관리법 및 소방청 질의회신집 기반 실시간 대화형 자문.

---

## 💻 빠른 시작 (Quick Start)

### 1. 저장소 클론 및 가상환경 설정
```bash
git clone https://github.com/dlrnrtls12-dev/hazmat-cop.git
cd hazmat-cop

# Python 가상환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\activate   # Windows PowerShell / CMD
# source .venv/bin/activate # Linux / macOS
```

### 2. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
copy .env.example .env
# .env 파일을 열고 필요한 API 키를 입력합니다 (기본 오프라인 기능은 키 없이도 동작)
```

### 4. 서버 실행
```bash
python app.py
# 또는 Windows에서 run_app.bat 더블 클릭
```
- **PC 브라우저 접속**: `http://localhost:8000`
- **모바일(스마트폰/태블릿) 접속**: PC 웹 화면 우측 상단의 **[📱 모바일 연결]** 버튼을 누르고 화면에 나타난 QR 코드를 스마트폰 기본 카메라로 스캔하거나, 표시된 로컬 IP(`http://192.168.x.x:8000`)로 접속합니다. (동일 Wi-Fi 환경)

### 5. 외부(LTE/5G) 현장 단속용 원격 접속
현장 출동 시 외부 LTE/5G 환경에서 PC에 구동된 서버로 접속하려면:
```bash
run_remote.bat
# 또는 npx localtunnel --port 8000
```
생성되는 공용 HTTPS 주소를 통해 스마트폰이나 태블릿에서 즉시 접속할 수 있습니다.

### 6. 모바일 홈 화면 추가 (PWA 앱 모드)
스마트폰 브라우저(사파리/크롬) 메뉴에서 **[홈 화면에 추가]**를 누르면 상단 주소창이 제거되고 네이티브 앱처럼 전체 화면(Standalone App)으로 구동되며, 통신 음영 지역에서도 오프라인 모드가 자동 지원됩니다.

---

## ☁️ 클라우드 배포 (Cloud Deployment)

- **Docker 배포**:
  ```bash
  docker build -t hazmat-cop .
  docker run -p 8000:8000 hazmat-cop
  ```
- **Render / Railway 원클릭 배포**: 본 GitHub 저장소를 연결하면 `render.yaml` 및 `Procfile`을 통해 24시간 언제 어디서나 접속 가능한 퍼블릭 웹 서비스로 자동 배포됩니다.

---

## 🛠️ 기술 스택 (Tech Stack)

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, Jinja2
- **Frontend**: Vanilla JavaScript (ES6+), Tailwind CSS (CDN), Lucide Icons, html2pdf.js, qrcode.js
- **Mobile/PWA**: Service Worker, Web App Manifest, High-DPI Canvas Scaling
- **Data & APIs**: 법제처 국가법령정보 API, 소방청 국가위험물정보 API, 경기도 데이터드림 API
- **Deployment**: Docker, Render, Railway, Local Tunnel

---

## 📄 라이선스 (License)

이 프로젝트는 MIT 라이선스를 따릅니다.
