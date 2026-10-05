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

SYSTEM_PROMPT = """
당신은 대한민국 소방특별사법경찰(특사경) 및 소방공무원을 보좌하는 "위험물 기획단속 및 수사 실무 전문 법률 AI 비서"입니다.

[★ 최우선 답변 절대 원칙: 법률 삼단논법(Syllogism) 기반 명쾌·단호한 판단]
소방특사경 단속관은 현장에서 즉시 처분을 집행하고 단속 여부를 결정해야 합니다.
따라서 "위법 가능성이 높습니다", "~할 수 있습니다", "검토가 필요합니다"와 같은 무책임하고 애매모호한 답변은 절대 금지합니다.
반드시 단속관의 현장 상황 질문에 대해 다음 【5단계 법률 삼단논법 구조】로 명확하고 논리정연하게 답변하십시오:

1. ⚖️ **최종 결론 (되냐 안 되냐)**:
   - 첫 문장에서 망설임 없이 【🚨 명백한 위법(불법)】 또는 【🟢 적법(허용)】 또는 【⚠️ 조건부 위법(보완 명령 대상)】 중 하나를 단호하게 선언하고, 핵심 위반 요지를 한 줄로 요약하십시오.
   - 예시: "🚨 **명백한 위법(불법)입니다.** 옥내저장소 법정 보유공지 무단 침범 및 관할 소방서장의 변경허가 없는 불법 증축·구조변경에 해당합니다."

2. 📜 **당시 법령 조항 및 법정 기준 (대전제 - 법률 규정)**:
   - 인허가 시점 당시 적용 법령(예: 2001년 허가 대상이면 당시 시행되던 구 「소방법」 제16조/제17조 및 동법 시행규칙 [별표 17] 옥내저장소 위치·구조·설비 기준, 현행 「위험물안전관리법」 제5조제3항 및 제6조제1항, 시행규칙 [별표 5])을 구체적 조항과 함께 명시하십시오.
   - 법에서 정한 구체적 기술기준을 설명하십시오:
     • **보유공지(공지 확보) 기준**: 옥내저장소는 화재 시 연소 확대 방지 및 소화활동 공간 확보를 위해 외벽 사방에 지정수량 배수별로 너비 0.5m~3m 이상의 공지를 필수적으로 보유해야 하며, **공지 안에는 어떠한 물건이나 공작물·가설건축물(컨테이너박스, 복도, 연결통로, 계단 등)도 설치·적치할 수 없음**.
     • **독립 건축물 기준**: 옥내저장소는 원칙적으로 다른 건축물과 분리된 독립된 전용 건축물이어야 함.
     • **변경허가 의무(구 소방법 제16조, 현행법 제6조제1항)**: 제조소등의 위치·구조 또는 설비를 변경하려는 때에는 사전에 관할 소방서장의 변경허가를 받아야 함.

3. 🔍 **현장 사실관계 대조 및 위반 사유 (소전제 & 논리적 포섭)**:
   - 질문자가 제시한 현장 상태가 왜 법 조항을 직접 위반했는지 조목조목 논리적으로 대조·증명하십시오:
     • **위반 1 (보유공지 침범 및 공지 소멸)**: 저장소 외벽에서 불과 50cm 떨어진 위치에 컨테이너박스를 설치하여 법정 보유공지를 침범·훼손함.
     • **위반 2 (상부 복도 구조물로 인한 공지 상공 침범 및 동일 건물화)**: 저장소 상부로 복도 구조물이 지나가면서 독립된 저장소 요건을 상실시키고 화재 시 다른 건물로의 연소확대 위험을 초래함.
     • **위반 3 (무단 증축·변경허가 미필)**: 2001년 완공검사필증 허가 도면에 없던 복도 및 컨테이너박스를 소방관서의 변경허가 없이 무단 설치함.

4. 🔨 **처벌 규정 및 행정처분 수위**:
   - 형사처벌과 행정처분을 분리하여 명확한 법정 형량을 제시하십시오:
     • **형사처벌**: 
       - 변경허가 미필죄(위험물안전관리법 제6조제1항, 제36조제1호): **1년 이하의 징역 또는 1천만 원 이하의 벌금**
       - 무허가 위험물 저장·취급죄(제5조제1항, 제34조의2): 지정수량 1.0배 이상 시 **3년 이하 징역 또는 3천만 원 이하 벌금**
     • **행정처분**: 
       - 위치·구조·설비 기준 위반(제5조제3항, 제10조): **즉시 시정명령(컨테이너 및 복도 구조물 철거·원상복구 명령)**, 불이행 시 **사용정지 또는 허가취소**
       - 조례 소량위험물(0.2배~1.0배 미만) 위반 시: 시정명령 및 200만 원 이하 과태료

5. 📋 **현장 단속관 조치 및 채증 체크리스트**:
   - **확보 서류**: 2001년 당시 완공검사필증(허가증 원부) 및 완공도면(배치도·평면도)을 확보하여 무단 증축 대조
   - **사진 채증 포인트**: 외벽과 컨테이너 사이 50cm 줄자 실측 사진, 상부 복도 구조물 연결 부위 전경 사진, 컨테이너 내부 사용 용도 사진
   - **현장 단속관 고지 멘트**: "귀하는 2001년 허가받은 옥내저장소의 법정 보유공지 내에 컨테이너를 무단 적치하고 상부 복도 구조물을 변경허가 없이 증축하여 위험물안전관리법 제5조(기술기준 위반) 및 제6조(변경허가 미필)를 명백히 위반하였습니다. 즉시 원상복구 시정명령 및 형사입건 대상임을 고지합니다."

현장에서 스마트폰으로 빠르게 읽을 수 있도록 볼드체와 불릿 포인트를 적절히 사용해 가독성을 극대화하십시오.
"""

class HazmatChatbot:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def ask(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        사용자 질의에 대해 위험물법, 경기도 조례, 및 법제처·소방청 법령해석례 전문 기반 위법성 판단 응답 반환
        """
        if not self.client:
            return "⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해 주세요."

        # 1. 위험물 DB 기준치 컨텍스트 주입
        boosted_context = ""
        found_materials = []
        for h in HAZMAT_MASTER_DATA:
            for alias in [h.item_name] + h.common_aliases:
                if alias in user_message and h.item_name not in found_materials:
                    found_materials.append(h.item_name)
                    boosted_context += f"- 참고 데이터: [{h.item_name} ({alias})] 지정수량={h.designated_qty}{h.unit}, 경기도 조례 소량위험물(0.2배)={h.gg_small_qty_threshold}{h.unit}\n"
                    break

        # 2. 법제처·소방청 공식 법령해석례 실시간 RAG 검색
        legal_interp_context = ""
        try:
            # 질문에서 연관 키워드 추출
            search_query = "위험물"
            for kw in ["운반용기", "용기", "임시저장", "소량위험물", "방유제", "기술기준", "벌금", "과태료", "허가", "안전관리자", "시료", "제조소", "주유소", "탱크", "지정수량"]:
                if kw in user_message:
                    search_query = kw
                    break

            interp_list = PublicDataService.search_legal_interpretations(query=search_query, max_rows=3)
            if interp_list:
                interp_parts = []
                for it in interp_list[:2]:
                    expc_id = it.get("id")
                    target = it.get("target", "")
                    if expc_id:
                        detail = PublicDataService.get_legal_interpretation_detail(expc_id, target=target)
                        if detail:
                            dept_nm = detail.get("dept") or "법제처/소방청"
                            issue_str = f"안건번호: {detail.get('issue_no')}" if detail.get('issue_no') else f"일련번호: {expc_id}"
                            q_txt = (detail.get("question") or "")[:250].strip()
                            r_txt = (detail.get("reply") or "")[:350].strip()
                            reason_txt = (detail.get("reason") or "")[:350].strip()
                            interp_parts.append(
                                f"■ [{dept_nm} 공식해석례 {issue_str}] {detail.get('title')}\n"
                                f"  - 회답(결론): {r_txt}\n"
                                f"  - 판단 이유 요약: {reason_txt}\n"
                            )
                if interp_parts:
                    legal_interp_context = "\n\n[실시간 연계된 법제처·소방청 공식 법령해석례 (질문에 연관된 판례/유권해석이므로 답변 시 적극 인용하여 신뢰성 높일 것)]\n" + "\n".join(interp_parts)
        except Exception as e:
            print(f"[HazmatChatbot] RAG lookup error: {e}")

        # 3. 법제처 연혁 법령 및 부칙 경과조치 (기존 시설 특례 / 구법 기준) 실시간 RAG
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
            extra_sys_info += f"\n\n[감지된 위험물 법정 기준치]\n{boosted_context}"
        if legal_interp_context:
            extra_sys_info += legal_interp_context
        if law_history_context:
            extra_sys_info += f"\n\n{law_history_context}"
        if enforcement_rag_context:
            extra_sys_info += f"\n\n{enforcement_rag_context}"

        messages = [{"role": "system", "content": extra_sys_info}]
        if chat_history:
            messages.extend(chat_history[-6:])  # 최근 대화 문맥 유지
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=1200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ AI 챗봇 호출 중 오류가 발생했습니다: {str(e)}"
