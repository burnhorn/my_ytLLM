import os
import re
import yt_dlp
import whisper
import traceback
import streamlit as st

# --- 도우미 함수 정의 ---
def sanitize_filename(title):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
    sanitized = sanitized.replace(" ", "_")
    return sanitized[:100]

def yt_get(yt_url, download_path='/tmp/', output_format='mp3'):
    st.write(f"'{yt_url}' 에서 오디오 다운로드 시도 중...")
    filepath = None
    try:
        st.write("영상 정보 사전 확인 중...")
        info_opts = { 'quiet': True, 'noplaylist': True, 'skip_download': True }
        with yt_dlp.YoutubeDL(info_opts) as ydl_info:
             info = ydl_info.extract_info(yt_url, download=False)
             title = info.get('title', 'untitled_video')
             sanitized_title = sanitize_filename(title)
             filename = f"{sanitized_title}.{output_format}"

             os.makedirs(download_path, exist_ok=True)
             filepath = os.path.join(download_path, filename)
             st.write(f"영상 제목: {title}")
             st.write(f"저장될 파일 경로 (예상): {filepath}")
    except Exception as e:
         st.error(f"영상 정보 확인 중 오류 발생: {str(e)}")
         return None
    if not filepath:
        st.error("오류: 최종 파일 경로를 결정할 수 없습니다.")
        return None
    filepath_template = os.path.splitext(filepath)[0]
    final_ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': output_format, 'preferredquality': '192',}],
        'noplaylist': True,
        'outtmpl': filepath_template,
        'keepvideo': False,
        'progress_hooks': [lambda d: print(d['status'])]
    }
    try:
        st.write("다운로드 및 변환 중...")
        with yt_dlp.YoutubeDL(final_ydl_opts) as ydl:
            ydl.download([yt_url])
        if os.path.exists(filepath):
            st.success(f"다운로드 및 변환 완료: '{filepath}'")
            return filepath
        else:
            st.error(f"오류: 최종 오디오 파일 '{filepath}' 생성 확인 불가.")
            return None
    except Exception as e:
        st.error(f"오디오 다운로드 중 오류 발생 (유형: {type(e).__name__}): {str(e)}")
        return None


def transcribe_audio_whisper(audio_filepath, model_size="base"):
    if not audio_filepath or not os.path.exists(audio_filepath):
        st.error(f"오류: 텍스트 변환할 오디오 파일을 찾을 수 없습니다: {audio_filepath}")
        return None
    st.write(f"오디오 파일 '{audio_filepath}' 텍스트 변환 중 (Whisper '{model_size}' 모델 사용)...")
    try:
        st.write(f"Whisper '{model_size}' 모델 로딩 중...")
        model = whisper.load_model(model_size)
        st.write("모델 로딩 완료.")
        st.write("텍스트 변환 실행 중...")
        result = model.transcribe(audio_filepath, fp16=False, language="en")
        st.success("텍스트 변환 완료!")
        transcribed_text = result["text"]
        return transcribed_text.strip() if transcribed_text else ""
    except Exception as e:
        st.error(f"Whisper 텍스트 변환 중 오류 발생: {e}")
        traceback.print_exc()
        return None
    finally:
        if audio_filepath and os.path.exists(audio_filepath):
            st.write(f"임시 오디오 파일 '{audio_filepath}' 삭제 중...")
            try:
                os.remove(audio_filepath)
                st.write("임시 오디오 파일 삭제 완료.")
            except Exception as e_del:
                st.warning(f"임시 오디오 파일 삭제 중 오류: {e_del}")

