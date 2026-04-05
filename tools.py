import traceback
from typing import Type, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from utils import yt_get, transcribe_audio_whisper
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Tool 클래스 정의 ---
class YouTubeUrlInput(BaseModel): youtube_url: str = Field(description="...")
class ReviewTextInput(BaseModel): text_content: str = Field(description="...")
class ImagePromptInput(BaseModel): prompt: str = Field(description="...")

# Tool 1: YouTubeTranscriptionTool
class YouTubeTranscriptionTool(BaseTool):
    name: str = "youtube_transcription_tool"
    description: str = "주어진 YouTube 영상 URL의 오디오를 다운로드하고 텍스트로 변환합니다. 변환된 텍스트(자막)를 반환합니다."
    args_schema: Type[BaseModel] = YouTubeUrlInput
    model_size: str = "base"
    def _run(self, youtube_url: str) -> str:
        try:
            print(f"--- YouTubeTranscriptionTool: '{youtube_url}' 처리 시작 ---")
            audio_path = yt_get(youtube_url) 
            if not audio_path: return "오류: YouTube 오디오 다운로드에 실패했습니다."
            transcribed_text = transcribe_audio_whisper(audio_path, model_size=self.model_size)
            if transcribed_text is not None:
                print(f"--- YouTubeTranscriptionTool: 변환 성공 ---")
                return transcribed_text
            else: return "오류: 오디오 텍스트 변환에 실패했습니다."
        except Exception as e: return f"오류: YouTube 처리 중 예외 발생: {e}"
    async def _arun(self, youtube_url: str) -> str: return self._run(youtube_url)

# Tool 2: ReviewGeneratorTool
class ReviewGeneratorTool(BaseTool):
    name: str = "review_generator_tool"
    description: str = "주어진 텍스트 내용(YouTube 자막)을 바탕으로 영상 콘텐츠에 대한 리뷰를 생성합니다."
    args_schema: Type[BaseModel] = ReviewTextInput
    llm: ChatGoogleGenerativeAI
    def _run(self, text_content: str) -> str:
        try:
            print("--- ReviewGeneratorTool: 리뷰 생성 시도 ---")
            prompt = f"""
                    당신은 전문 콘텐츠 리뷰어입니다. 당신의 임무는 아래 제공된 YouTube 영상 자막을 분석하여, 시청자들이 영상의 핵심 내용을 단번에 파악할 수 있도록 구조화된 리뷰를 작성하는 것입니다.

                    다음 지침을 반드시 따라주세요:
                    1.  매력적인 제목: 영상의 주제를 잘 나타내는 흥미로운 제목을 한 줄로 작성하세요.
                    2.  핵심 요약: 영상 전체 내용을 2-3문장으로 간결하게 요약하세요.
                    3.  주요 포인트: 영상에서 가장 중요한 메시지나 정보 3가지를 불렛 포인트(•)로 정리하세요.
                    4.  추천 대상: 이 영상이 어떤 사람들에게 특히 유용할지 추천 대상을 명시하세요. (예: "이 영상은 액션 마니아에게 강력 추천합니다.")
                    5.  톤앤매너: 친절하고 이해하기 쉬운 어조를 사용하세요.

                    --- 자막 내용 ---
                    {text_content}
                    --- 자막 내용 끝 ---

                    위 지침에 따라 리뷰를 작성해 주세요.
                    """
            response = self.llm.invoke(prompt)
            review = response.content
            print(f"--- ReviewGeneratorTool: 리뷰 생성 완료 ---")
            return review
        except Exception as e: return f"오류: 리뷰 생성 중 오류 발생: {e}"

# Tool 3: ImageGeneratorTool
class ImageGeneratorTool(BaseTool):
    name: str = "image_generator_tool"
    description: str = "주어진 텍스트 프롬프트(생성된 리뷰)를 기반으로 이미지를 생성합니다. 성공 시 확인 메시지를 반환합니다."
    args_schema: Type[BaseModel] = ImagePromptInput
    llm: ChatGoogleGenerativeAI
    last_generated_image_base64: Optional[str] = None
    def _run(self, prompt: str) -> str:
        self.last_generated_image_base64 = None
        try:
            print(f"--- ImageGeneratorTool: '{prompt[:50]}...' 기반 *썸네일* 생성 시도 ---")
            image_generation_prompt = f"""
            Create a compelling thumbnail image for a YouTube video based on the following review summary.
            The image should visually capture the essence and mood of the review, focusing on key themes like connection, nature, conflict, and emotion.
            **Do not include any text or words in the image itself.**
            Style: Cinematic, vibrant, slightly mystical, high-detail.

            Review Summary to Visualize:
            {prompt}
            """
            message = { "role": "user", "content": image_generation_prompt }
            response = self.llm.invoke([message], generation_config=dict(response_modalities=["TEXT", "IMAGE"]))
            image_base64 = None
            if isinstance(response.content, list) and len(response.content) > 0:
                image_element = None
                if isinstance(response.content[0], dict) and response.content[0].get('type') == 'image_url': image_element = response.content[0]
                elif len(response.content) >= 2 and isinstance(response.content[1], dict) and response.content[1].get('type') == 'image_url': image_element = response.content[1]
                if image_element:
                    image_part_dict = image_element.get('image_url')
                    if isinstance(image_part_dict, dict):
                         data_uri = image_part_dict.get('url')
                         if data_uri and isinstance(data_uri, str) and data_uri.startswith('data:image'): image_base64 = data_uri.split(',')[-1]
            if image_base64:
                print(f"--- ImageGeneratorTool: 이미지 생성 및 Base64 추출 성공 ---")
                self.last_generated_image_base64 = image_base64
                return "이미지 생성에 성공했습니다."
            else:
                 print(f"ImageGeneratorTool 오류: 유효한 이미지 데이터를 추출하지 못했습니다. Response: {response}")
                 return "오류: 이미지 생성 응답에서 유효한 이미지 데이터를 찾을 수 없습니다."
        except Exception as e:
            print(f"ImageGeneratorTool 오류 발생: {e}")
            traceback.print_exc()
            return f"오류: 이미지 생성 중 오류 발생: {e}"
