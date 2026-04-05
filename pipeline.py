import traceback

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import ImageGeneratorTool, YouTubeTranscriptionTool, ReviewGeneratorTool

# --- 메인 파이프라인 클래스 정의 ---
# Agent 및 Executor 초기화 로직
class YouTubeReviewPipeline:
    def __init__(self, agent_model_name: str = "gemini-2.0-flash",
                 review_model_name: str = "gemini-2.0-flash",
                 image_model_name: str = "models/gemini-2.0-flash-exp-image-generation",
                 whisper_model_size: str = "base",
                 agent_temperature: float = 0,
                 review_temperature: float = 0.7):
        print("\n--- YouTubeReviewPipeline 초기화 시작 ---")
        self.agent_llm = ChatGoogleGenerativeAI(model=agent_model_name, temperature=agent_temperature)
        self.review_llm = ChatGoogleGenerativeAI(model=review_model_name, temperature=review_temperature)
        try:
            self.image_llm = ChatGoogleGenerativeAI(model=image_model_name)
            print(f"이미지 생성 모델 로드: {image_model_name}")
            self.image_tool = ImageGeneratorTool(llm=self.image_llm) # 인스턴스 변수로 저장
        except Exception as e:
            print(f"경고: 이미지 생성 모델({image_model_name}) 로드 실패: {e}")
            self.image_llm = None
            self.image_tool = None

        self.youtube_tool = YouTubeTranscriptionTool(model_size=whisper_model_size)
        self.review_tool = ReviewGeneratorTool(llm=self.review_llm)

        self.tools = [self.youtube_tool, self.review_tool]
        if self.image_tool:
            self.tools.append(self.image_tool)
            print("모든 Tool (자막, 리뷰, 이미지)이 설정되었습니다.")
        else:
             print("경고: 이미지 생성 Tool이 설정되지 않았습니다.")

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", """You are an assistant that processes YouTube videos.
                Your goal is to:
                1. Take a YouTube video URL as input.
                2. Use the 'youtube_transcription_tool' to get the video's transcript.
                3. Use the 'review_generator_tool' with the transcript to create a review of the video.
                (If available) 4. Use the 'image_generator_tool' with the generated review to create a relevant thumbnail image (no text in image). This tool will return a success message.
                5. Finally, return ONLY the generated review text. Do not include the image tool's success message in your final answer. Just output the review.
                If any step fails, report the error clearly."""),
                ("placeholder", "{chat_history}"), 
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        self.agent = create_tool_calling_agent(self.agent_llm, self.tools, self.prompt_template)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
        print("--- YouTubeReviewPipeline 초기화 완료 ---")

    def run(self, youtube_url: str) -> dict:
        print(f"\n--- 파이프라인 실행 시작 (URL: {youtube_url}) ---")
        
        if self.image_tool: self.image_tool.last_generated_image_base64 = None
        final_review = "리뷰 생성에 실패했습니다."
        image_base64 = None

        try:
            response = self.agent_executor.invoke({"input": f"Process the YouTube video at this URL: {youtube_url}"})
            print("\n--- Agent 실행 완료 ---")
            agent_output = response.get('output')
            if isinstance(agent_output, str) and not agent_output.startswith("오류:"): final_review = agent_output
            else: print(f"경고: Agent가 리뷰 텍스트를 정상 반환 못함. Output: {agent_output}")
            if self.image_tool: image_base64 = self.image_tool.last_generated_image_base64
        except Exception as e:
            print(f"\nAgent 실행 중 오류 발생: {e}")
            traceback.print_exc()
            final_review = f"Agent 실행 오류: {e}"
        print("--- 파이프라인 실행 종료 ---")
        return {"review": final_review, "image_base64": image_base64}
