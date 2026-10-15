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

[★ 『위험물 민원 질의응답 사례집(인쇄본)』 공식 답변 서식 절대 준수 원칙]
소방공무원과 특사경은 현장에서 즉시 법 집행을 해야 하므로 "상황에 따라 다를 수 있습니다", "검토가 필요합니다" 같은 애매모호하거나 두루뭉술한 답변은 절대 금지합니다.
『위험물 민원 질의응답 사례집(인쇄본)』의 표준 양식에 따라 명확한 법적 근거에 입각하여 다음과 같이 답변하십시오:

【회신 요지 (핵심 결론)】
- "답 : [명확하고 단정적인 1줄 결론 선언]"
  (예: "답 : 보유공지 내 장치물 등을 설치할 수 없음", "답 : 배수의 합계가 1.5배이므로 무허가 저장(법 제5조 위반)에 해당함", "답 : 최대 탱크 용량의 110% 이상을 확보하여야 함")

【상세 이유 및 법적 해석】
1. 법령의 입법 취지 및 해당 시설기준(위치·구조·설비)의 정의 명시.
2. 질의된 현장 사실관계를 법령 요건에 단계별(1, 2, 3)로 직접 대조·포섭.
3. 예외 또는 특례 인정 여부를 법령 단서 규정에 근거하여 명확히 판정.

【관련 법령 및 행정규칙】
- 적용 법조문 조·항·호 및 시행령/시행규칙 별표를 정확히 명시 (예: 「위험물안전관리법」 제5조제1항, 동법 시행령 별표 1 제4류, 동법 시행규칙 별표 4 Ⅰ. 제2호 등).

【실무 유의사항 및 참고자료】
- 처벌 규정(형사처벌 형량 및 과태료 액수) 또는 소방청/법제처 공식 유권해석, 현장 채증 포인트 제시.

※ 항목별로 불릿 포인트를 활용하여 가독성을 극대화하고, 법 조항에 기반한 단호한 법적 결론을 내리십시오."""

# =========================================================================
# 솔루션 1: 법정 절대 불변 수치 하드 매핑 사전 (수치 착오·환각 원천 차단)
# =========================================================================
STATUTORY_HARD_CONSTANTS = [
    {
        "keywords": ["임시저장", "임시 보관", "임시취급"],
        "fact": "★ [법정 절대 불변 수치: 임시저장] 「위험물안전관리법」 제5조제2항 단서 및 시행규칙 제6조에 따른 관할 소방서장의 임시저장 승인 최대 기간은 '90일 이내'임. (30일이 절대 아니며 반드시 '90일 이내'로 명시할 것)"
    },
    {
        "keywords": ["안전관리자", "퇴사", "퇴직", "후임"],
        "fact": "★ [법정 절대 불변 수치: 안전관리자 선임] 「위험물안전관리법」 제15조제3항에 따라 안전관리자 퇴직 시 후임자 선임 기한은 퇴직일로부터 '30일 이내'이며, 대리자 지정 기간도 최대 '30일 이내'임. 선임 후 소방서 신고는 '14일 이내'(법 제15조제4항)임."
    },
    {
        "keywords": ["지위승계", "경매", "낙찰", "상속"],
        "fact": "★ [법정 절대 불변 수치: 지위승계] 「위험물안전관리법」 제10조제3항에 따라 경매 낙찰 또는 상속 등으로 제조소등 시설을 인수한 자의 지위승계 신고 기한은 인수일로부터 '30일 이내'임."
    },
    {
        "keywords": ["방유제", "방유턱", "유효용량"],
        "fact": "★ [법정 절대 불변 수치: 방유제 용량] 「위험물안전관리법 시행규칙」 별표 6 제17호에 따라 옥외탱크 방유제 용량은 탱크 1기인 경우 '해당 탱크 용량의 110% 이상', 2기 이상인 경우 '최대 탱크 용량의 110% 이상'임. 방유제 높이는 0.5m 이상 3.0m 이하임."
    },
    {
        "keywords": ["간이탱크", "간이저장"],
        "fact": "★ [법정 절대 불변 수치: 간이탱크저장소] 「위험물안전관리법 시행규칙」 별표 9에 따라 1개소당 설치 가능한 간이탱크는 최대 '3기 이하', 각 탱크 용량은 '600L 이하'이며 동일 품명 중복 설치 불가함."
    },
    {
        "keywords": ["내압시험", "수압시험", "배관시험"],
        "fact": "★ [법정 절대 불변 수치: 배관 내압시험] 「위험물안전관리법 시행규칙」 별표 4 Ⅰ 제13호에 따라 위험물 배관 수압시험은 '최대사용압력(설계압력)의 1.5배 이상'이며, 기압시험 시 비활성기체로 '1.1배 이상'임."
    },
    {
        "keywords": ["접지저항", "정전기"],
        "fact": "★ [법정 절대 불변 수치: 정전기 접지설비] 「위험물안전관리법 시행규칙」 별표 4 Ⅰ 제11호에 따라 정전기 제거를 위한 접지설비의 접지저항값은 '100Ω 이하'임."
    },
    {
        "keywords": ["수용성", "용해도"],
        "fact": "★ [법정 절대 불변 수치: 수용성 판정] 「위험물안전관리법 시행령」 별표 1 비고 16호에 따라 수용성이란 1기압 20℃에서 '물 100g에 용해되는 양이 10g 이상'인 물질을 말함."
    },
    {
        "keywords": ["알코올", "손소독제", "에탄올", "소독용"],
        "fact": "★ [법정 절대 불변 수치: 알코올류 농도] 「위험물안전관리법 시행령」 별표 1 제4류에 따라 탄소수 1~3 포화1가 알코올 함유량이 '60중량% 이상'인 경우 제4류 알코올류(지정수량 400L) 위험물에 해당함."
    },
    {
        "keywords": ["인화성고체", "고형알코올", "고체연료"],
        "fact": "★ [법정 절대 불변 수치: 인화성고체] 「위험물안전관리법 시행령」 별표 1 제2류 제6호에 따라 고형알코올 등 1기압에서 '인화점이 40℃ 미만인 고체'는 제2류 인화성고체(지정수량 1,000kg)에 해당함."
    },
    {
        "keywords": ["소화난이도", "포소화설비", "난이도등급"],
        "fact": "★ [법정 절대 불변 수치: 옥외탱크 소화난이도 Ⅰ등급] 「위험물안전관리법 시행규칙」 별표 17에 따라 옥외탱크저장소는 '액표면적 40㎡ 이상'이거나 '높이 6m 이상' 또는 '지정수량 100배 이상' 중 하나에 해당하면 소화난이도등급 Ⅰ등급으로 고정식 포소화설비 의무 설치 대상임."
    },
    {
        "keywords": ["매설 깊이", "토피", "이송배관", "도로 지하"],
        "fact": "★ [법정 절대 불변 수치: 배관 매설 깊이] 「위험물안전관리법 시행규칙」 별표 15에 따라 도로 하부 매설 깊이는 '노면으로부터 1.5m 이상', 일반 부지는 '1.2m 이상'임."
    }
]

class HazmatChatbot:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def ask(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None, model_id: Optional[str] = None, images: Optional[List[str]] = None) -> str:
        return self.ask_with_meta(user_message, chat_history, model_id=model_id, images=images)["response"]

    def ask_with_meta(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None, model_id: Optional[str] = None, images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        사용자 질의 및 사진/영상 시각 증거에 대해 위험물법, 경기도 조례, 및 법제처·소방청 법령해석례 전문 기반 위법성 판단 응답 및 모델 메타 반환
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

        # 1. 솔루션 1: 법정 절대 불변 수치 하드 매핑 (Hard Grounding)
        hard_facts_context = ""
        for item in STATUTORY_HARD_CONSTANTS:
            if any(k in user_message for k in item["keywords"]):
                hard_facts_context += f"{item['fact']}\n"

        # 2. 솔루션 2: 위험물 DB 기준치 및 HazmatEngine 결정론적 자동 연동
        boosted_context = ""
        found_materials = []
        for h in HAZMAT_MASTER_DATA:
            for alias in [h.item_name] + h.common_aliases:
                if alias in user_message and h.item_name not in found_materials:
                    found_materials.append(h.item_name)
                    boosted_context += f"• [{h.item_name}] 품명={h.class_name}, 지정수량={h.designated_qty}{h.unit}, 조례 0.2배 기준={h.gg_small_qty_threshold}{h.unit}\n"
                    break

        # 수량 및 품명이 함께 언급된 경우 결정론적 계산 엔진(HazmatEngine) 사전 수행
        calc_pre_context = ""
        try:
            import re
            extracted_items = []
            for h in HAZMAT_MASTER_DATA:
                for alias in [h.item_name] + h.common_aliases:
                    if alias in user_message:
                        qty_match = re.search(rf"{re.escape(alias)}[^\d]*(\d+(?:\.\d+)?)\s*(?:L|리터|kg|킬로|톤)?", user_message)
                        if qty_match:
                            extracted_items.append(InspectionItem(chemical_name=alias, quantity=float(qty_match.group(1))))
                        break
            if extracted_items:
                calc_res = HazmatEngine.calculate_and_assess(InspectionContext(items=extracted_items, location_type="unauthorized_place"))
                calc_pre_context = (
                    f"\n[★ 결정론적 계산기(HazmatEngine) 판정치: 수치 임의 변경 금지]\n"
                    f"• 총 지정수량 배수: {calc_res.total_multiple}배\n"
                    f"• 위법성 판정: {'형사처벌 대상(1.0배 이상, 3년/3천만원)' if calc_res.is_designated_qty_or_more else ('조례 과태료 대상(0.2배 이상 ~ 1.0배 미만)' if calc_res.is_gg_ordinance_applicable else '지정수량 미만')}\n"
                )
        except Exception as e:
            pass

        # 3. 법제처·소방청 공식 법령해석례 실시간 RAG 검색
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

        # 4. 법제처 연혁 법령 및 부칙 경과조치 실시간 RAG
        law_history_context = ""
        try:
            from services.law_history_service import LawHistoryService
            law_history_context = LawHistoryService.generate_law_history_context(user_message)
        except Exception as e:
            print(f"[HazmatChatbot] Law history lookup error: {e}")

        # 5. 소방특사경 핵심 수사전략 & 소방청 공식 업무지침 27종 & KB_049(50선 DB) RAG
        enforcement_rag_context = ""
        try:
            from services.enforcement_knowledge_service import EnforcementKnowledgeService
            enforcement_rag_context = EnforcementKnowledgeService.get_rag_context(user_message)
        except Exception as e:
            print(f"[HazmatChatbot] Enforcement knowledge lookup error: {e}")

        extra_sys_info = SYSTEM_PROMPT
        if hard_facts_context:
            extra_sys_info += f"\n\n[★ 법정 절대 불변 수치 - 모델 임의 변경·추정 절대 금지]\n{hard_facts_context}"
        if calc_pre_context:
            extra_sys_info += calc_pre_context
        if boosted_context:
            extra_sys_info += f"\n\n[법정 기준치]\n{boosted_context}"
        if legal_interp_context:
            extra_sys_info += legal_interp_context
        if law_history_context:
            extra_sys_info += f"\n\n{law_history_context}"
        if enforcement_rag_context:
            extra_sys_info += f"\n\n{enforcement_rag_context}"

        extra_sys_info += (
            "\n\n[솔루션 3: 네거티브 가드레일 - 회피성 표현 절대 금지]\n"
            "- '사안에 따라 다를 수 있습니다', '검토가 필요합니다', '소방서에 확인해 보아야 합니다' 같은 회피성 문구를 최종 결론으로 두지 마십시오.\n"
            "- 소방서 재량/허가 사항인 경우에도 '원칙상 불가(위법)하며, 관할 소방서장의 설치허가(특례승인)를 받아야 함'과 같이 단정형으로 종결하십시오."
        )

        if images and len(images) > 0:
            extra_sys_info += (
                "\n\n[★ 현장 사진/동영상 프레임 시각 증거 정밀 판독 지침]\n"
                "- 사용자가 첨부한 현장 사진 또는 동영상 프레임을 정밀 판독하십시오.\n"
                "- 1단계: 위험물 용기 형태(드럼통, 플라스틱 말통, IBC탱크, 탱크로리 등) 및 수량을 식별하십시오.\n"
                "- 2단계: 용기 표면의 위험물 경고라벨, GHS 그림문자, 품명, 화기엄금 표지판, UN 번호를 판독하십시오.\n"
                "- 3단계: 무허가 적치 장소(공장 마당, 야외 나대지 등) 보관 상태 및 안전거리/보유공지 위반 여부를 확인하십시오.\n"
                "- 4단계: 지정수량 배수를 계산하고, 1.0배 이상 형사입건(법 제5조) 또는 0.2배 이상 조례 위반 과태료 여부를 명확히 단정하여 판정하십시오."
            )

        if "[실시간 음성통화]" in user_message or "voice_call" in user_message:
            extra_sys_info += (
                "\n\n[★ 실시간 음성 통화(전화) 모드 특별 지침 - 절대 준수]\n"
                "- 현재 단속관과 실시간 음성(전화) 통화 중입니다.\n"
                "- 음성 합성(TTS)으로 단속관 귀에 직접 실시간으로 낭독되므로, 마크다운 기호(**, ##, -, •, 번호매기기)나 특수문자, 괄호를 일절 사용하지 마십시오.\n"
                "- 첫 문장에 핵심 결론(품명, 계산 배수, 위법 여부)을 즉시 단정적으로 말씀하십시오.\n"
                "- 이어지는 두 번째 문장에 적용 법조문과 단속관이 현장에서 취해야 할 수사 조치를 간결하고 명확한 구어체로 2~3문장 이내로만 답변하십시오."
            )

        messages = [{"role": "system", "content": extra_sys_info}]

        # 토큰 절약: 최근 4개(2턴) 대화만 유지하고, 이전 어시스턴트 답변은 200자로 축약
        if chat_history:
            for h in chat_history[-4:]:
                content = h.get("content", "")
                if h.get("role") == "assistant" and len(content) > 200:
                    content = content[:200] + "..."
                messages.append({"role": h.get("role"), "content": content})

        if images and len(images) > 0:
            user_prompt = user_message.strip() if user_message else "첨부된 현장 사진/영상의 위험물 품명, 수량, 표시사항 및 위법성 여부를 정밀 분석해 주십시오."
            user_content = [{"type": "text", "text": user_prompt}]
            for img in images[:4]:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
            messages.append({"role": "user", "content": user_content})
        else:
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
