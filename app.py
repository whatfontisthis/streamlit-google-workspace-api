import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
import time
import os
import logging

logging.basicConfig(level=logging.INFO)

# 페이지 설정
st.set_page_config(
    page_title="프로젝트 간트 차트", layout="wide", initial_sidebar_state="expanded"
)

# 타이틀 및 설명
st.title("프로젝트 간트 차트")
st.markdown("Google Sheets의 프로젝트 데이터를 실시간으로 시각화합니다.")


# Google Sheets 연결 함수
@st.cache_resource
def get_gspread_client():
    try:
        st.write("Google API 자격 증명 확인 중...")

        if "GOOGLE_APPLICATION_CREDENTIALS" in st.secrets:
            st.write("자격 증명 정보를 찾았습니다.")
            credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]

            # 자격 증명 정보 일부 확인 (보안 정보는 가리기)
            safe_info = {
                "type": credentials_info.get("type", "없음"),
                "project_id": credentials_info.get("project_id", "없음"),
                "client_email": credentials_info.get("client_email", "없음"),
            }
            st.write("자격 증명 정보:", safe_info)

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            try:
                credentials = Credentials.from_service_account_info(
                    credentials_info, scopes=scopes
                )
                gc = gspread.authorize(credentials)
                st.success("Google API 연결 성공!")
                return gc
            except Exception as e:
                st.error(f"자격 증명 처리 오류: {e}")
                return None
        else:
            st.error("Google API 자격 증명이 설정되지 않았습니다.")
            st.write("secrets.toml 파일을 확인하세요.")
            return None
    except Exception as e:
        st.error(f"Google 연결 중 예상치 못한 오류: {e}")
        return None


# 사이드바 설정
st.sidebar.header("설정")
sheet_url = st.sidebar.text_input(
    "Google 스프레드시트 URL 또는 ID",
    help="예: https://docs.google.com/spreadsheets/d/1abc123def456...",
)

# 시트 이름 입력
sheet_name = st.sidebar.text_input(
    "시트 이름 (비워두면 첫 번째 시트 사용)", value="시트1"
)

# 자동 새로고침 간격 설정
refresh_interval = st.sidebar.slider(
    "자동 새로고침 간격 (초)", min_value=10, max_value=300, value=60
)

# 차트 표시 옵션
show_complete = st.sidebar.checkbox("완료된 작업 표시", True)
color_by = st.sidebar.selectbox(
    "색상 구분 기준", ["우선순위", "프로젝트명", "진행률(%)"]
)

# 새로고침 버튼
manual_refresh = st.sidebar.button("수동 새로고침")


# 스프레드시트에서 데이터 가져오기
def fetch_data_from_sheet(gc, sheet_url, sheet_name=None):
    try:
        st.write(f"스프레드시트 연결 시도: {sheet_url}")

        # URL에서 스프레드시트 ID 추출
        if "docs.google.com/spreadsheets/d/" in sheet_url:
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            st.write(f"추출된 스프레드시트 ID: {sheet_id}")
        else:
            sheet_id = sheet_url
            st.write(f"입력된 스프레드시트 ID: {sheet_id}")

        # 스프레드시트 열기
        spreadsheet = gc.open_by_key(sheet_id)

        # 시트 선택 (이름이 지정되지 않은 경우 첫 번째 시트 사용)
        if sheet_name:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                st.warning(
                    f"'{sheet_name}' 시트를 찾을 수 없습니다. 첫 번째 시트를 사용합니다."
                )
                worksheet = spreadsheet.sheet1
        else:
            worksheet = spreadsheet.sheet1

        # 데이터프레임으로 변환
        df = get_as_dataframe(worksheet, evaluate_formulas=True, skiprows=0)

        # 빈 행 제거
        df = df.dropna(how="all")

        # 열 이름 정리 (앞뒤 공백 제거)
        df.columns = df.columns.str.strip()

        # 필요한 열이 있는지 확인
        required_columns = [
            "프로젝트명",
            "세부 작업",
            "시작일",
            "종료일",
            "진행률(%)",
            "우선순위",
        ]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"필요한 열이 없습니다: {col}")
                return None

        # 날짜 열 처리
        df["시작일"] = pd.to_datetime(df["시작일"], errors="coerce")
        df["종료일"] = pd.to_datetime(df["종료일"], errors="coerce")

        # 빈 날짜 데이터 제거
        df = df.dropna(subset=["시작일", "종료일"])

        # 작업명 생성 (프로젝트명: 세부 작업)
        df["작업명"] = df["프로젝트명"] + ": " + df["세부 작업"]

        return df

    except Exception as e:
        st.error(f"데이터 가져오기 오류: {e}")
        return None


def create_gantt_chart(df, color_field, show_complete=True):
    try:
        # 완료된 작업 필터링 (선택 시)
        if not show_complete:
            df = df[df["진행률(%)"] < 100]

        # 날짜 타입 확인 및 변환
        st.write(
            "날짜 데이터 타입 확인:",
            f"시작일: {type(df['시작일'].iloc[0])}, 종료일: {type(df['종료일'].iloc[0])}",
        )

        # 데이터프레임 복사 및 날짜를 문자열로 변환
        plot_df = df.copy()

        # 간트 차트용 데이터 준비 (날짜를 문자열로 유지)
        plot_df["시작일_str"] = plot_df["시작일"].dt.strftime("%Y-%m-%d")
        plot_df["종료일_str"] = plot_df["종료일"].dt.strftime("%Y-%m-%d")

        # 현재 날짜
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 날짜 범위 계산 (원본 datetime 사용)
        min_date = df["시작일"].min()
        max_date = df["종료일"].max()

        st.write(
            f"날짜 범위: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
        )

        # 간트 차트 생성 (문자열 날짜 사용)
        fig = px.timeline(
            plot_df,
            x_start="시작일",  # 원래 datetime 열 사용
            x_end="종료일",  # 원래 datetime 열 사용
            y="작업명",
            color=color_field,
            color_discrete_map=(
                {
                    "높음": "#ff6961",  # 빨간색
                    "중간": "#ffb347",  # 주황색
                    "낮음": "#77dd77",  # 녹색
                }
                if color_field == "우선순위"
                else None
            ),
            hover_data=["진행률(%)", "메모"],
            labels={"작업명": "작업", "시작일": "시작", "종료일": "종료"},
            height=600,
        )

        # 차트 레이아웃 설정
        fig.update_layout(
            xaxis=dict(type="date", title="날짜"),
            yaxis=dict(autorange="reversed", title=""),
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(title=color_field),
            plot_bgcolor="rgba(240, 240, 240, 0.5)",
        )

        # 오늘 날짜를 Unix 타임스탬프(밀리초)로 변환
        today_timestamp = datetime.now().timestamp() * 1000  # 밀리초 단위로 변환

        # 오늘 날짜 선 추가
        fig.add_vline(
            x=today_timestamp,  # 타임스탬프 사용
            line_width=2,
            line_dash="dash",
            line_color="red",
            annotation_text="오늘",
            annotation_position="top right",
        )

        # 진행률 표시 (바 위에 텍스트로)
        for i in range(len(plot_df)):
            fig.add_annotation(
                x=(
                    plot_df["시작일"].iloc[i]
                    + (plot_df["종료일"].iloc[i] - plot_df["시작일"].iloc[i]) / 2
                ).strftime("%Y-%m-%d"),
                y=plot_df["작업명"].iloc[i],
                text=f"{plot_df['진행률(%)'].iloc[i]}%",
                showarrow=False,
                font=dict(color="white", size=10),
                bgcolor="rgba(0,0,0,0.5)",
                borderpad=2,
            )

        return fig

    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {e}")
        import traceback

        st.code(traceback.format_exc())
        return None


# 안내 메시지 컨테이너
info_container = st.empty()
data_timestamp = st.empty()
chart_container = st.container()

# 연결 확인 및 데이터 가져오기
if sheet_url:
    # Google Sheets 클라이언트 가져오기
    gc = get_gspread_client()

    if gc:
        # 연결 횟수 및 마지막 연결 시간 추적
        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = datetime.now() - timedelta(
                seconds=refresh_interval * 2
            )

        # 자동 새로고침 또는 수동 새로고침 확인
        time_since_refresh = (
            datetime.now() - st.session_state.last_refresh
        ).total_seconds()
        should_refresh = manual_refresh or time_since_refresh >= refresh_interval

        if should_refresh:
            with info_container:
                with st.spinner("Google Sheets에서 데이터를 불러오는 중..."):
                    df = fetch_data_from_sheet(gc, sheet_url, sheet_name)
                    st.session_state.last_refresh = datetime.now()
                    st.session_state.data = df
        else:
            # 이전에 가져온 데이터 사용
            df = st.session_state.get("data")

        # 데이터가 있으면 차트 표시
        if df is not None and not df.empty:
            data_timestamp.info(
                f"마지막 업데이트: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')} · {len(df)}개 작업 · {refresh_interval}초마다 자동 갱신"
            )

            # 데이터 미리보기
            with st.expander("데이터 미리보기"):
                st.dataframe(
                    df[
                        [
                            "프로젝트명",
                            "세부 작업",
                            "시작일",
                            "종료일",
                            "진행률(%)",
                            "우선순위",
                        ]
                    ]
                )

            # 간트 차트 생성
            with chart_container:
                fig = create_gantt_chart(df, color_by, show_complete)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        elif not should_refresh:
            info_container.info(
                "데이터를 아직 불러오지 않았습니다. '수동 새로고침' 버튼을 클릭하세요."
            )
        elif df is not None and df.empty:
            info_container.warning(
                "스프레드시트에 데이터가 없거나 필요한 열을 찾을 수 없습니다."
            )
    else:
        info_container.error("Google API 연결 설정이 필요합니다.")
else:
    # 스프레드시트 URL이 제공되지 않은 경우 안내 메시지 표시
    info_container.info("왼쪽 사이드바에 Google 스프레드시트 URL을 입력하세요.")

    # 설정 방법 안내
    st.markdown(
        """
    ## 설정 방법
    
    ### 1. Google API 및 서비스 계정 설정
    
    1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트를 만듭니다.
    2. Google Sheets API와 Google Drive API를 활성화합니다.
    3. 서비스 계정을 만들고 JSON 키 파일을 다운로드합니다.
    4. 이 JSON 파일의 내용을 Streamlit의 'secrets.toml' 파일에 추가합니다.
    
    ### 2. 스프레드시트 공유 설정
    
    1. 스프레드시트를 서비스 계정 이메일(JSON 파일에 있음)과 공유합니다.
    2. 스프레드시트 URL 또는 ID를 왼쪽 사이드바에 입력합니다.
    
    ### 3. Streamlit Secrets 설정
    
    'secrets.toml' 파일에 다음 형식으로 추가합니다:
    
    ```toml
    [GOOGLE_APPLICATION_CREDENTIALS]
    type = "service_account"
    project_id = "프로젝트ID"
    private_key_id = "개인 키 ID"
    private_key = "개인 키 내용"
    client_email = "서비스 계정 이메일"
    client_id = "클라이언트 ID"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "클라이언트 인증서 URL"
    ```
    """
    )

# 자동 새로고침을 위한 스크립트
if sheet_url and gc:
    st.write(
        f"""
    <script>
        setTimeout(function() {{
            window.location.reload();
        }}, {refresh_interval * 1000});
    </script>
    """,
        unsafe_allow_html=True,
    )
