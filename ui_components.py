import streamlit as st
import base64

def render_sidebar():
    """사이드바 UI를 렌더링하고 사용자 입력을 반환합니다."""
    st.sidebar.header("영상 URL 입력")
    youtube_url_input = st.sidebar.text_input("YouTube 영상 URL을 여기에 붙여넣으세요:")
    process_button = st.sidebar.button("리뷰 및 이미지 생성 시작")
    return youtube_url_input, process_button

def display_results(review, image_base64_str):
    """생성된 리뷰와 이미지를 화면에 표시합니다."""
    st.markdown("---")

    if review:
        st.subheader("생성된 리뷰")
        st.markdown(review)
        st.markdown("---")

    if image_base64_str:
        st.subheader("생성된 썸네일 이미지")
        try:
            image_base64_data = image_base64_str
            missing_padding = len(image_base64_data) % 4
            if missing_padding:
                image_base64_data += '=' * (4 - missing_padding)
            image_data = base64.b64decode(image_base64_data)
            st.image(image_data, caption="생성된 썸네일 이미지", use_container_width=True)
        except base64.binascii.Error as decode_error:
            st.error(f"오류: Base64 디코딩 실패: {decode_error}")
        except Exception as e:
            st.error(f"오류: 이미지 표시에 실패했습니다: {e}")
    elif st.session_state.get('processing') is False and review is not None:
        st.warning("이미지를 생성하지 못했거나 찾을 수 없습니다.")

def display_initial_info():
    """초기 안내 메시지를 표시합니다."""
    if not st.session_state.get('processing') and not st.session_state.get('review'):
        st.info("사이드바에 YouTube URL을 입력하고 버튼을 눌러 시작하세요.")