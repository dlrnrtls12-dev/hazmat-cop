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

[법적 판단 기준]
1. 「위험물안전관리법」 (국가법):
   - 지정수량 1.0배 이상 무허가 저장·취급(제5조제1항, 제34조의2): 3년 이하의 징역 또는 3천만 원 이하의 벌금 (형사입건 대상)
   - 임시저장·취급 승인 미필(제5조제2항)
   - 제조소등 위치·구조·설비 기준 위반(제5조제3항): 시정명령 및 1천만원 이하 벌금
   - 변경허가 미필(제6조제1항): 1년 이하 징역 또는 1천만원 이하 벌금
   - 위험물 운반용기 표시·수납기준 위반(제20조): ★지정수량 미만이라도 200만원 이하 과태료 부과 대상!
   - 출입·검사 거부·방해·기피(제27조제6항): 1년 이하 징역 또는 1천만원 이하 벌금

2. 「경기도 위험물 안전관리 조례」 (자치법규 - ★2024.9.21. 개정 반영):
   - 소량위험물 관리 범위가 종전 1/2(0.5배) 이상에서 【지정수량의 1/5(0.2배) 이상 ~ 1.0배 미만】으로 대폭 확대됨.
   - 소량위험물 저장·취급 기술기준 위반 시: 시정명령, 불이행 시 200만 원 이하 과태료.
   - 공사장 등 임시취급시설: 안전관리책임자 지정 및 부재 시 직무대행자 지정 의무.

3. 「법제처·소방청 공식 법령해석례」 (유권해석):
   - 질문과 관련하여 주어지는 법제처/소방청 법령해석례 데이터가 있다면, 해당 안건번호(예: 16-0134 등)와 유권해석 회답 및 판단 이유를 명시적으로 인용하여 답변의 법적 신뢰도를 극대화하십시오.

[답변 원칙 및 출력 포맷]
단속관이 현장 상황을 질문하면 반드시 다음 4단계 구조로 명쾌하게 답변하십시오:
1. ⚖️ **위법 여부 판단**: [위법성 명백 / 위법 가능성 높음 / 적법 / 추가 확인 필요] 중 하나를 명시하고 요약
2. 📜 **적용 법조문 및 공식 법령해석례**: 위험물안전관리법, 경기도 조례, 및 관련 법제처·소방청 공식 유권해석례(안건번호 명시)를 교차 설명
3. 🔨 **처벌 및 행정처분 수위**: 형사처벌(징역/벌금)과 행정처분(시정명령/과태료)을 분리하여 명확히 설명
4. 📋 **현장 단속관 조치 및 채증 체크리스트**: 현장에서 당장 해야 할 행동(고지 멘트, 확보해야 할 서류, 사진 채증 포인트)

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

        extra_sys_info = SYSTEM_PROMPT
        if boosted_context:
            extra_sys_info += f"\n\n[감지된 위험물 법정 기준치]\n{boosted_context}"
        if legal_interp_context:
            extra_sys_info += legal_interp_context
        if law_history_context:
            extra_sys_info += f"\n\n{law_history_context}"

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
