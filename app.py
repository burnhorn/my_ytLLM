import os
import traceback
import streamlit as st

from pipeline import YouTubeReviewPipeline
from ui_components import render_sidebar, display_results, display_initial_info # UI 함수 임포트

google_api_key = None

try:
    if "GOOGLE_API_KEY" in st.secrets:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
        key_source = "Streamlit Secrets"
except Exception:
    pass

if not google_api_key:
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if google_api_key:
        key_source = "환경 변수"

if google_api_key:
    if 'GOOGLE_API_KEY' not in os.environ:
        os.environ['GOOGLE_API_KEY'] = google_api_key
else:
    st.sidebar.error("오류: Streamlit Secrets 또는 환경 변수 어디에도 'GOOGLE_API_KEY'가 설정되지 않았습니다!")
    st.stop()

@st.cache_resource
def load_pipeline():
    """파이프라인 객체를 로드하고 반환합니다."""
    pipeline = YouTubeReviewPipeline(
        agent_model_name="gemini-2.0-flash",
        review_model_name="gemini-2.0-flash",
        image_model_name="models/gemini-2.0-flash-exp-image-generation",
        whisper_model_size="base"
    )
    return pipeline


st.title("YouTube 영상 리뷰 및 썸네일 생성기")
st.write("YouTube 영상 URL을 입력하면 AI가 자막을 추출하여 리뷰를 작성하고, 관련 썸네일 이미지를 생성합니다.")

try:
    pipeline = load_pipeline()
except Exception as e:
    st.error(f"파이프라인 로딩 중 오류 발생: {e}")
    st.error("Google API Key 설정 및 모델 이름을 확인하세요.")
    st.stop()

youtube_url_input, process_button = render_sidebar()

if 'review' not in st.session_state:
    st.session_state.review = None
if 'image_base64' not in st.session_state:
    st.session_state.image_base64 = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

if process_button and youtube_url_input:
    st.session_state.review = None
    st.session_state.image_base64 = None
    st.session_state.processing = True

    with st.spinner('영상을 처리하고 있습니다... 잠시만 기다려주세요 (몇 분 정도 소요될 수 있습니다).'):
        try:
            result = pipeline.run(youtube_url_input)
            st.session_state.review = result['review']
            st.session_state.image_base64 = result['image_base64']
            st.success("처리 완료!")
        except Exception as e:
            st.error(f"처리 중 오류 발생: {e}")
            traceback.print_exc()

    st.session_state.processing = False
    st.rerun()

display_results(st.session_state.review, st.session_state.image_base64)
display_initial_info()