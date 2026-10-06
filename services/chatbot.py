"""
services/chatbot.py
위험물 단속 전문 AI 법률 상담 챗봇 엔진
- 위험물안전관리법 및 경기도 위험물 안전관리 조례 기반 위법성 판단
- OpenAI GPT 모델 연동 및 결정론적 계산 엔진(HazmatEngine) 하이브리드 결합
"""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

from core.hazmat_db import HAZMAT_MASTER_DATA, find_hazmat
from core.calculator import HazmatEngine, InspectionContext, InspectionItem
from services.public_data_service import PublicDataService

load_dotenv()

SYSTEM_PROMPT = """당신은 대한민국 소방특별사법경찰(특사경) 및 소방공무원을 보좌하는 "위험물 기획단속 및 수사 실무 전문 법률 AI 비서"입니다.

[★ 최우선 답변 절대 원칙: 법률 삼단논법(Syllogism) 5단계 구조 및 토큰 절약 원칙]
소방특사경 단속관은 현장에서 즉시 처분을 집행해야 하므로 "위법 가능성이 있습니다", "검토가 필요합니다" 같은 애매모호한 답변은 절대 금지합니다.
정확성은 완벽히 유지하되 불필요한 인사말, 미사여구, 중복 설명을 배제하고 다음 【5단계 구조】로 핵심만 고밀도로 압축 서술하십시오:

1. ⚖️ **최종 결론**: 첫 문장에서 망설임 없이 【🚨 명백한 위법(불법)】 / 【🟢 적법(허용)】 / 【⚠️ 조건부 위법(보완명령 대상)】 중 하나를 단호히 선언하고 핵심 위반 요지 1줄 요약.
2. 📜 **법령 조항 및 법정 기준 (대전제)**: 인허가 당시 적용 법령(구 소방법 또는 현행 위험물안전관리법 제5조/제6조 등)과 법정 기술기준(보유공지, 방유제, 독립건축물 등) 명시.
3. 🔍 **사실관계 대조 및 위반 사유 (소전제 & 포섭)**: 현장 사실관계가 왜 법 조항 및 기준을 직접 위반했는지 핵심 사실 2~3개 불릿으로 간결·명료하게 대조.
4. 🔨 **처벌 규정 및 행정처분**:
   - 형사처벌: 무허가(제5조/제34조의2, 3년/3천만원), 변경허가 미필(제6조/제36조, 1년/1천만원) 등 구체적 형량 제시.
   - 행정처분: 시정명령, 사용정지, 조례 소량위험물 과태료(200만원 이하) 구분 명시.
5. 📋 **단속관 조치 및 채증 체크리스트**: 확보 서류(완공검사필증/도면), 필수 사진 채증 포인트(줄자 실측 등), 피의자 대상 1줄 현장 고지 멘트.

※ 스마트폰으로 즉시 판독할 수 있도록 불릿 포인트를 활용하여 항목당 2~3줄 이내로 고밀도 압축 작성하십시오."""

class HazmatChatbot:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def ask(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None, model_id: Optional[str] = None) -> str:
        return self.ask_with_meta(user_message, chat_history, model_id=model_id)["response"]

    def ask_with_meta(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        사용자 질의에 대해 위험물법, 경기도 조례, 및 법제처·소방청 법령해석례 전문 기반 위법성 판단 응답 및 모델 메타 반환
        """
        import time
        start_time = time.time()

        if not self.client:
            return {
                "response": "⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해 주세요.",
                "model_used": "none",
                "elapsed_ms": 0,
                "mode": "error"
            }

        # 1. 위험물 DB 기준치 컨텍스트 주입 (토큰 최적화: 압축된 1줄 형태)
        boosted_context = ""
        found_materials = []
        for h in HAZMAT_MASTER_DATA:
            for alias in [h.item_name] + h.common_aliases:
                if alias in user_message and h.item_name not in found_materials:
                    found_materials.append(h.item_name)
                    boosted_context += f"• [{h.item_name}] 지정수량={h.designated_qty}{h.unit}, 조례 소량기준(0.2배)={h.gg_small_qty_threshold}{h.unit}\n"
                    break

        # 2. 법제처·소방청 공식 법령해석례 실시간 RAG 검색 (토큰 최적화: 최상위 1건, 핵심 요지 압축)
        legal_interp_context = ""
        try:
            search_query = "위험물"
            for kw in ["운반용기", "용기", "임시저장", "소량위험물", "방유제", "기술기준", "벌금", "과태료", "허가", "안전관리자", "시료", "제조소", "주유소", "탱크", "지정수량"]:
                if kw in user_message:
                    search_query = kw
                    break

            interp_list = PublicDataService.search_legal_interpretations(query=search_query, max_rows=2)
            if interp_list:
                for it in interp_list[:1]:
                    expc_id = it.get("id")
                    target = it.get("target", "")
                    if expc_id:
                        detail = PublicDataService.get_legal_interpretation_detail(expc_id, target=target)
                        if detail:
                            dept_nm = detail.get("dept") or "법제처/소방청"
                            issue_str = f"안건 {detail.get('issue_no')}" if detail.get('issue_no') else f"ID {expc_id}"
                            r_txt = (detail.get("reply") or "")[:150].strip()
                            reason_txt = (detail.get("reason") or "")[:150].strip()
                            legal_interp_context = (
                                f"\n[관련 유권해석 참고: {dept_nm} {issue_str}]\n"
                                f"• 회답: {r_txt}\n"
                                f"• 이유: {reason_txt}\n"
                            )
                            break
        except Exception as e:
            print(f"[HazmatChatbot] RAG lookup error: {e}")

        # 3. 법제처 연혁 법령 및 부칙 경과조치 실시간 RAG
        law_history_context = ""
        try:
            from services.law_history_service import LawHistoryService
            law_history_context = LawHistoryService.generate_law_history_context(user_message)
        except Exception as e:
            print(f"[HazmatChatbot] Law history lookup error: {e}")

        # 4. 소방특사경 핵심 수사전략 & 소방청 공식 업무지침 27종 RAG
        enforcement_rag_context = ""
        try:
            from services.enforcement_knowledge_service import EnforcementKnowledgeService
            enforcement_rag_context = EnforcementKnowledgeService.get_rag_context(user_message)
        except Exception as e:
            print(f"[HazmatChatbot] Enforcement knowledge lookup error: {e}")

        extra_sys_info = SYSTEM_PROMPT
        if boosted_context:
            extra_sys_info += f"\n\n[법정 기준치]\n{boosted_context}"
        if legal_interp_context:
            extra_sys_info += legal_interp_context
        if law_history_context:
            extra_sys_info += f"\n\n{law_history_context}"
        if enforcement_rag_context:
            extra_sys_info += f"\n\n{enforcement_rag_context}"

        messages = [{"role": "system", "content": extra_sys_info}]

        # 토큰 절약: 최근 4개(2턴) 대화만 유지하고, 이전 어시스턴트 답변은 200자로 축약
        if chat_history:
            for h in chat_history[-4:]:
                content = h.get("content", "")
                if h.get("role") == "assistant" and len(content) > 200:
                    content = content[:200] + "..."
                messages.append({"role": h.get("role"), "content": content})

        messages.append({"role": "user", "content": user_message})

        try:
            from services.agent_model_manager import AgentModelManager
            llm_res = AgentModelManager.call_agent_llm("main_chatbot", messages, override_max_tokens=700, override_model_id=model_id)
            if llm_res["success"]:
                elapsed_ms = llm_res.get("elapsed_ms") or int((time.time() - start_time) * 1000)
                return {
                    "response": llm_res["content"],
                    "model_used": llm_res.get("model", model_id or "gpt-4o-mini"),
                    "elapsed_ms": elapsed_ms,
                    "mode": llm_res.get("mode", "llm")
                }
            else:
                # 2차 긴급 안전망: OpenAI gpt-4o-mini로 즉시 무중단 답변 생성
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    try:
                        emergency_client = OpenAI(api_key=openai_key)
                        em_res = emergency_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            max_tokens=700,
                            temperature=0.3
                        )
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        return {
                            "response": em_res.choices[0].message.content,
                            "model_used": "gpt-4o-mini (긴급 자동 전환)",
                            "elapsed_ms": elapsed_ms,
                            "mode": "fallback_llm"
                        }
                    except Exception as em_err:
                        print(f"[HazmatChatbot] Emergency OpenAI fallback failed: {em_err}")

                from services.multi_agent_service import MultiAgentService
                offline_summary = MultiAgentService._generate_offline_agent_reply("tactics_agent", user_message, "")
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "response": f"💡 [안내: AI 모델 일시 지연으로 내장 특사경 룰 엔진으로 즉시 전문 답변을 제공합니다]\n\n" + offline_summary,
                    "model_used": "offline-heuristic",
                    "elapsed_ms": elapsed_ms,
                    "mode": "offline"
                }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "response": f"⚠️ AI 챗봇 호출 중 오류가 발생했습니다: {str(e)}",
                "model_used": "error",
                "elapsed_ms": elapsed_ms,
                "mode": "error"
            }
