# YouTube LLM Agent: AI 기반 영상 리뷰 & 썸네일 생성 파이프라인

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white) ![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-8E75B2?logo=google&logoColor=white) ![Whisper](https://img.shields.io/badge/OpenAI_Whisper-412991?logo=openai&logoColor=white)

YouTube 영상의 URL만 입력하면 AI가 오디오를 추출하고 텍스트로 변환하여 내용을 요약하고 그에 맞는 시각적 썸네일을 자동 생성해 주는 LangChain Agent 기반 PoC(Proof of Concept) 프로젝트입니다.

<img width="1920" height="950" alt="Image" src="https://github.com/user-attachments/assets/ec52e39a-2a84-4616-9ad8-ec391193af62" />

<img width="1918" height="955" alt="Image" src="https://github.com/user-attachments/assets/d09ecbf4-b49c-442f-9dd6-ddc0b6d3c0f2" />

<img width="1920" height="947" alt="Image" src="https://github.com/user-attachments/assets/6d2f56e3-b8eb-4320-8d92-eaee426b028d" />


## 프로젝트 개요

- **개발 기간**: 2025.05 ~ 2025.06 (1인 개인 프로젝트)
- **목적**: AICC(인공지능 콜센터) 및 미디어 분석 서비스의 핵심 파이프라인인 '비정형 데이터(음성) -> STT(텍스트 변환) -> LLM 분석/생성'의 기술적 흐름을 직접 구현하고 LangChain Agent의 Tool-Calling 동작 원리를 깊이 이해하기 위해 기획했습니다.
- **참고사항**: 본 프로젝트는 YouTube 다운로드(yt-dlp) 시 발생하는 IP/Cookie 기반 Bot Block 정책으로 인해 로컬 환경에 최적화된 PoC 형태로 구현되었습니다.

## 아키텍쳐 및 흐름
![Image](https://github.com/user-attachments/assets/c5f71f2c-7f25-4de0-9816-21090b70299c)
1. **사용자 입력**: Streamlit UI를 통해 YouTube URL 입력
2. **Agent 오케스트레이션**: `AgentLLM`이 프롬프트 지침에 따라 어떤 Tool을 순서대로 사용할지 결정
3. **도구 실행**:
   - `YouTubeTranscriptionTool`: yt-dlp로 오디오 추출 후 Whisper 모델로 STT 변환
   - `ReviewGeneratorTool`: 변환된 자막을 Gemini 모델에 전달하여 리뷰 생성
   - `ImageGeneratorTool`: 리뷰 내용을 기반으로 이미지 생성 프롬프트를 구성하여 썸네일 생성
4. **결과 반환**: 최종 리뷰 텍스트와 Base64 형태의 이미지를 UI에 렌더링

## 기술스택

- **Backend & LLM Framework**: Python, LangChain
- **AI Models**: Google Gemini 2.0 Flash (Text & Image Gen), OpenAI Whisper (STT)
- **External Tools**: yt-dlp, FFmpeg
- **Frontend**: Streamlit

## 엔지니어링 결정 사항

### 1. LLM Agent의 토큰 제한(Context Length) 최적화 및 구조 개선

- **문제**: `ImageGeneratorTool`이 생성한 이미지 데이터(Base64)가 매우 방대하여 이를 Agent의 작업 내역으로 전달할 경우 LLM의 처리 토큰 한계를 초과해 시스템이 다운되는 문제 발생.
- **해결**: 멀티미디어 데이터와 텍스트 컨텍스트의 **관심사를 분리**했습니다. Image Tool은 이미지 생성 성공 여부(Text)만 Agent에게 반환하고 무거운 Base64 데이터는 클래스 인스턴스(`last_generated_image_base64`)에 별도로 상태를 저장했습니다. 이후 파이프라인 종료 시 딕셔너리 형태로 텍스트와 이미지를 병합하여 UI로 전달함으로써 토큰 병목을 해결했습니다.

### 2. 멀티모달 프롬프트 엔지니어링 및 파싱 최적화

- **문제**: 이미지 생성 요청 시 이미지가 아닌 텍스트(리뷰 내용)가 그려진 이미지가 반환되거나 모델이 지원하지 않는다는 오류 발생.
- **해결**:
  - 응답 파싱 로직을 개선하여 `response_modalities=["TEXT", "IMAGE"]` 형태로 명확하게 요청.
  - 프롬프트에 "Strictly no text in the image"라는 제약 조건을 명시하고 단순 요약이 아닌 시각적 메타포(분위기, 핵심 키워드)를 표현하도록 프롬프트 구조를 고도화했습니다.

### 3. 미디어 파일 전처리(yt-dlp) 예외 처리

- **문제**: 영상 제목에 특수문자가 포함된 경우 확장자 처리가 누락되어 Whisper 모델이 오디오 파일을 찾지 못하는 파이프라인 중단 현상 발생.
- **해결**: 파일명 정규화 함수를 추가하고 다운로드 예상 경로와 실제 FFmpeg 변환 후 경로를 로깅 및 추적하는 디버깅 프로세스를 통해 예기치 않은 I/O 에러를 방어했습니다.

## 실행 방법

```bash
# 저장소 클론 및 패키지 설치
git clone [https://github.com/your-id/youtube-llm-agent.git](https://github.com/your-id/youtube-llm-agent.git)
pip install -r requirements.txt

# streamlit 실행
streamlit run app.py
```
