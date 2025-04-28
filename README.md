# 📊 Google Sheets 간트 차트 시각화

Google Sheets 데이터를 사용하여 프로젝트 간트 차트를 실시간으로 시각화하는 Streamlit 애플리케이션입니다.

## 주요 기능

- 🔄 **실시간 연동**: Google Sheets 데이터를 자동으로 새로고침
- 📈 **인터랙티브 간트 차트**: Plotly 기반의 시각적이고 직관적인 프로젝트 타임라인
- 🎨 **맞춤 시각화**: 우선순위별 색상 구분, 진행률 표시
- ⏱️ **자동 갱신**: 설정 가능한 간격으로 데이터 자동 업데이트
- 🔍 **필터링 옵션**: 완료된 작업 숨기기 등 다양한 표시 옵션

## 설치 방법

### 1. 필요 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. Google Cloud 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. Google Sheets API와 Google Drive API 활성화
3. 서비스 계정 생성 및 JSON 키 다운로드
4. Google 스프레드시트를 서비스 계정 이메일과 공유 (편집자 권한)

### 3. Streamlit Secrets 설정

`.streamlit/secrets.toml` 파일 생성:

```toml
[GOOGLE_APPLICATION_CREDENTIALS]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

## 사용 방법

1. Streamlit 앱 실행:

```bash
streamlit run app.py
```

2. 왼쪽 사이드바에 Google 스프레드시트 URL 또는 ID 입력
3. 원하는 시트 이름 지정 (기본값: "시트1")
4. 갱신 간격 및 표시 옵션 설정
5. 간트 차트 확인 및 필요시 '수동 새로고침' 버튼 클릭

## 데이터 형식

스프레드시트는 다음 열을 포함해야 합니다:

- `ID`: 작업 ID
- `프로젝트명`: 프로젝트 이름
- `세부 작업`: 작업 세부 내용
- `시작일`: 작업 시작일 (YYYY-MM-DD 형식)
- `종료일`: 작업 종료일 (YYYY-MM-DD 형식)
- `진행률(%)`: 작업 진행률 (0-100)
- `우선순위`: 작업 우선순위 (높음, 중간, 낮음)
- `메모`: 추가 정보

## 기술 스택

- **Streamlit**: 웹 인터페이스 및 데이터 시각화
- **Google API Client**: Google Workspace와 통합
- **Plotly**: 인터랙티브 간트 차트 시각화
- **Pandas**: 데이터 처리 및 변환
- **gspread**: Google Sheets 데이터 액세스

## 주의 사항

- 서비스 계정 키는 안전하게 보관해야 합니다.
- 스프레드시트는 서비스 계정 이메일과 공유되어야 합니다.
- 기본 갱신 간격은 60초이며, 사이드바에서 조정 가능합니다.

## 라이선스

MIT License - 자유롭게 사용, 수정 및 배포 가능합니다.
