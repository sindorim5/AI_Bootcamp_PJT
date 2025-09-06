from typing import Dict, Any
from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState
from retrieval.vector_store import search_topic, search_topic_with_scores
from retrieval.cross_encoder_service import get_cross_encoder_service
import logging

logger = logging.getLogger(__name__)

class RetrieveAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str, use_cross_encoder: bool = True, plan_enabled: bool = False):
        super().__init__(
            system_prompt=(
                "You are the Retrieve Agent in an AI financial advisor system. "
                "Your role is to analyze retrieved financial news and reports "
                "based on the user's topic, capital, and risk level, and deliver "
                "a concise, factual summary in Korean. "
                "Rules:\n"
                "- Always answer in Korean.\n"
                "- Summarize only information supported by the retrieved documents.\n"
                "- Do not fabricate data. If data is missing, clearly state '정보 없음'.\n"
                "- Highlight key facts, market context, and investor-relevant insights.\n"
                "- Keep the output compact, structured, and easy to read for a busy investor.\n"
                "- Prioritize information from US and Korean economic/financial publications.\n"
                "- Avoid relying on Chinese language sources unless absolutely necessary.\n"
                "- Focus on authoritative sources like Bloomberg, Reuters, WSJ, Financial Times, "
                "한국경제, 매일경제, 이데일리, 서울경제 등."
            ),
            rag = rag,
            langfuse_session_id = langfuse_session_id,
            plan_enabled = plan_enabled
            )
        self.use_cross_encoder = use_cross_encoder

    def _retrieve_context(self, state: AgentState) -> AgentState:

        if self.rag == False:
            return {**state, "agent_id": 2, "context": ""}

        chat_state = state["chat_state"]
        topic = chat_state["topic"]
        capital = chat_state["capital"]
        risk_level = chat_state["risk_level"]

        # 크로스 인코더 사용 여부에 따라 다른 검색 방법 사용
        if self.use_cross_encoder:
            # 크로스 인코더를 사용한 고품질 검색
            documents_with_scores = search_topic_with_scores(
                topic=topic,
                capital=capital,
                risk_level=risk_level,
                use_cross_encoder=True,
                relevance_threshold=0.6
            )

            # 점수 정보를 포함하여 문서 추출
            documents = []
            relevance_scores = []
            for doc, score in documents_with_scores:
                documents.append(doc)
                relevance_scores.append(score)

            # 안전한 로깅 (빈 리스트 체크)
            if relevance_scores:
                logger.info(f"크로스 인코더 검색 결과: {len(documents)}개 문서, 점수 범위: {min(relevance_scores):.3f}~{max(relevance_scores):.3f}")
            else:
                logger.warning("크로스 인코더 검색 결과가 없습니다.")
        else:
            # 기존 방식으로 검색
            documents = search_topic(
                topic=topic,
                capital=capital,
                risk_level=risk_level,
                use_cross_encoder=False
            )
            relevance_scores = [1.0] * len(documents)

        # 검색 결과가 없는 경우 처리
        if not documents:
            logger.warning(f"주제 '{topic}'에 대한 검색 결과가 없습니다.")
            return {
                **state,
                "agent_id": 2,
                "retrieve_docs": [],
                "context": "검색 결과가 없습니다.",
                "relevance_scores": [],
                "cross_encoder_used": self.use_cross_encoder
            }

        # 중국어 문서 필터링 및 우선순위 조정
        filtered_documents = []
        for doc, score in zip(documents, relevance_scores):
            # 메타데이터에서 출처 확인
            source = doc.metadata.get("source", "").lower() if hasattr(doc, 'metadata') else ""

            # 미국/한국 경제 전문지 우선
            priority_sources = [
                "bloomberg", "reuters", "wsj", "ft.com", "financialtimes",
                "koreaherald", "koreatimes", "koreajoongangdaily",
                "hankyung", "mk.co.kr", "edaily", "sedaily", "biz.chosun",
                "hankookilbo", "donga", "joongang", "chosun"
            ]

            # 우선순위가 높은 출처는 앞에 배치
            if any(src in source for src in priority_sources):
                filtered_documents.insert(0, (doc, score))
            else:
                filtered_documents.append((doc, score))

        # 크로스 인코더 점수로 최종 정렬
        if self.use_cross_encoder and filtered_documents:
            filtered_documents.sort(key=lambda x: x[1], reverse=True)

        # 문서만 추출
        final_documents = [doc for doc, _ in filtered_documents]

        # 관련성 점수 정보를 메타데이터에 추가
        for i, (doc, score) in enumerate(filtered_documents):
            if hasattr(doc, 'metadata'):
                doc.metadata['relevance_score'] = score
                doc.metadata['final_rank'] = i + 1

        context = super()._format_context(final_documents)

        return {
            **state,
            "agent_id": 2,
            "retrieve_docs": final_documents,
            "context": context,
            "relevance_scores": relevance_scores,
            "cross_encoder_used": self.use_cross_encoder
            }

    def _create_prompt(self, state: AgentState) -> str:
        topic = state["chat_state"]["topic"]
        capital = state["chat_state"]["capital"]
        risk_level = state["chat_state"]["risk_level"]
        context = state["context"]
        cross_encoder_used = state.get("cross_encoder_used", False)

        logger.info(f"context: {context}")
        logger.info(f"state: {state}")

        # 크로스 인코더 사용 여부에 따른 프롬프트 조정
        cross_encoder_info = ""
        if cross_encoder_used:
            cross_encoder_info = (
                "\n[참고: 이 검색 결과는 크로스 인코더를 통해 관련성을 재평가하고 "
                "재순위화되었습니다. 더 정확하고 관련성 높은 정보를 제공합니다.]\n"
            )

        prompt = (
            f"사용자 프로필:\n"
            f"- 주제: '{topic}'\n"
            f"- 자본금: {capital}만원\n"
            f"- 위험성향: {risk_level} (1=보수적, 5=공격적)\n\n"
            "다음은 관련 금융 뉴스·리포트 검색 결과입니다:\n\n"
            f"{context}\n"
            f"{cross_encoder_info}\n"
            "Instructions:\n"
            "- 위 문서들에 근거하여 한국어로 요약하세요.\n"
            "- 아래 양식으로 작성해주세요.\n"
            "- 1) 핵심 요약\n"
            "- 2) 주요 데이터 포인트\n"
            "- 3) 리스크 및 모니터링 포인트\n"
            "- 각 항목별 주의 사항\n"
            "- 1) 핵심 요약은 3~5문장으로\n"
            "- 2) 주요 데이터 포인트와, 3) 리스크 및 모니터링 포인트는 불릿으로 간결히\n"
            "- 문서에 없는 내용은 추가하지 마세요.\n"
            "- 명확히 결과만 표시하고 추가 요청 같은 건 하지 말아주세요.\n"
            "- 미국과 한국의 경제 전문지 출처를 우선적으로 참고하세요.\n"
            "- 중국어 문서는 신뢰할 수 있는 번역이 있는 경우에만 참고하세요."
        )

        return prompt
