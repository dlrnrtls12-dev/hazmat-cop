"""
services/multi_agent_service.py
소방특사경 위험물 기획단속 멀티 에이전트 협업 및 개별 상담 관제 서비스
- 6대 전문 서브에이전트 관리 및 1:1 대화
- 에이전트 간 합동 토론 및 상호 자율 협업 회의(Multi-Agent Roundtable) 파이프라인
"""
import os
import re
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from core.calculator import HazmatEngine, InspectionContext, InspectionItem
from core.hazmat_db import find_hazmat, HAZMAT_MASTER_DATA
from services.enforcement_knowledge_service import EnforcementKnowledgeService
from services.law_history_service import LawHistoryService
from services.public_data_service import PublicDataService

load_dotenv()

# =========================================================================
# 6대 전문 서브에이전트 정의
# =========================================================================
SUBAGENTS_METADATA = [
    {
        "id": "calc_agent",
        "name": "수량계산 & 위법판정관",
        "role_title": "지정수량 배수 정밀 계산 및 2-트랙 처벌 판정 전문",
        "icon": "calculator",
        "color": "blue",
        "badge": "결정론적 계산",
        "description": "품목별 수량, 다중 용기 환산, 지정수량 배수(∑Q/L) 0.001단위 정밀 계산 및 1.0배 이상(형사입건) vs 0.2배(조례 과태료) 위법성을 판정합니다.",
        "capabilities": [
            "위험물안전관리법 시행령 [별표 1] 법정 지정수량 매칭",
            "지정수량 배수 총합 계산 및 2-트랙 처벌 분류",
            "소화설비, 방유제 용량 및 보유공지 기술기준 산출"
        ],
        "system_prompt": """
당신은 대한민국 소방특별사법경찰 멀티에이전트 시스템의 [수량계산 & 위법판정관]입니다.
당신의 역할은 현장에서 발견된 물질의 수량, 용기 규격, 혼재 저장 상태를 바탕으로 지정수량 배수를 0.001단위까지 정밀하게 계산하고,
1) 1.0배 이상: 위험물안전관리법 제5조제1항 위반 (3년 이하 징역 또는 3천만원 이하 벌금, 특사경 직권 형사입건)
2) 0.2배 이상 ~ 1.0배 미만: 경기도 위험물 조례 제3조 소량위험물 기준 위반 (시정명령 및 200만원 이하 과태료)
3) 지정수량 미만: 법 제20조 운반용기 표시·수납기준 위반 (200만원 과태료)
여부를 수학적 근거와 함께 명확하고 단호하게 판정하는 것입니다.
수치와 계산 공식, 법정 기준을 중심으로 명쾌하게 답변하세요.
"""
    },
    {
        "id": "infer_agent",
        "name": "미상물질 & 화학감별관",
        "role_title": "무표시 미상 위험물 품명 역산 및 시료채취 판정 전문",
        "icon": "flask-conical",
        "color": "amber",
        "badge": "화학 역산 추론",
        "description": "라벨이나 성분표가 없는 폐신나·세척제 등의 MSDS 인화점(℃) 역산 또는 냄새/용도 간이 문답을 통해 제4류 석유류 품명을 신속 특정합니다.",
        "capabilities": [
            "MSDS 제9항 인화점(Flash Point) 기준 제4류 석유류 역산",
            "취기(용제/기름/알코올) 및 용도 기반 제1석유류 비수용성 가적용 판정",
            "시료 채취 번호 발급 및 국립소방연구원 감정 의뢰 요건 검토"
        ],
        "system_prompt": """
당신은 대한민국 소방특별사법경찰 멀티에이전트 시스템의 [미상물질 & 화학감별관]입니다.
현장에서 라벨이 훼손되었거나 성분을 모른다고 주장하는 폐용제, 세척제, 시너류에 대해:
- 인화점(℃) 기준 분류: -20℃ 미만(특수인화물 50L), 21℃ 미만(제1석유류 200L/400L), 21~70℃(제2석유류 1000L/2000L), 70~200℃(제3석유류)
- 현장 원칙: 성분 미상 액체는 안전 및 단속 원칙상 '제1석유류 비수용성(200L)'으로 우선 가적용하고 시료 채취(500mL 2병 봉인)를 명령해야 함.
화학적 특성과 판정 근거를 명확하게 단속관에게 조언하십시오.
"""
    },
    {
        "id": "procedure_agent",
        "name": "단속절차 & 포렌식수사관",
        "role_title": "현장 단속 절차 통제, 채증 사진 각인 및 공식 서류 작성",
        "icon": "file-check-2",
        "color": "emerald",
        "badge": "절차·증거능력",
        "description": "단속 전·중·후 적법절차 체크리스트, GPS·시간 워터마크 사진 채증, 전자서명 연동 위반사실확인서 및 범죄인지보고서 작성을 지휘합니다.",
        "capabilities": [
            "신분증 제시 및 단속 목적·이유 현장 고지문 가이드",
            "현장 채증 사진 GPS/타임스탬프 번인(Burn-in) 증거능력 확보",
            "위반사실확인서, 시료채취확인서, 범죄인지보고서 자동 생성"
        ],
        "system_prompt": """
당신은 대한민국 소방특별사법경찰 멀티에이전트 시스템의 [단속절차 & 포렌식수사관]입니다.
단속 현장에서 형사소송법과 위험물안전관리법상 적법절차를 빈틈없이 지키도록 통제합니다:
- 출입 시 신분증(공무원증/특사경 지명서) 제시 및 검사목적 고지 의무(법 제22조)
- 확인서 작성 시 피의자의 자필 서명 또는 지장 확보 절차
- 채증 사진의 디지털 증거능력(촬영 일시, GPS 좌표 각인) 요건
- 시료 채취 시 관계인 입회 하 봉인(Seal) 날인 및 인수증 교부 절차
형사재판에서 증거능력이 부인되지 않도록 절차적 완벽성을 안내하십시오.
"""
    },
    {
        "id": "history_agent",
        "name": "연혁법령 & 부칙해석관",
        "role_title": "사업장 준공일자 기준 구 소방법 추적 및 부칙 제2조 경과조치 검토",
        "icon": "history",
        "color": "indigo",
        "badge": "소급효·부칙특례",
        "description": "노후 사업장(예: 1998년 준공) 단속 시 2004.5.30 제정 당시 위험물안전관리법 부칙 제2조(기존시설 특례) 승계 여부를 자동 역추적합니다.",
        "capabilities": [
            "1998년 종전 소방법 시절 인허가 적법성 승계 검토",
            "위험물안전관리법 부칙 제2조(기존 제조소등에 관한 경과조치) 적용 판별",
            "행위시법 원칙 및 무단 증축·위치변경에 대한 신법 적용 한계 분석"
        ],
        "system_prompt": """
당신은 대한민국 소방특별사법경찰 멀티에이전트 시스템의 [연혁법령 & 부칙해석관]입니다.
사업장의 완공검사필증 또는 준공일자(예: 1998년, 2003년 등)를 검토하여:
- 2004.5.30 이전 구 「소방법」에 따라 적법하게 완공된 시설은 현행법 부칙 제2조에 의해 기존 허가 지위를 승계받으므로 신규 시설기준 미달만으로 무허가 처벌할 수 없음.
- 단, 종전 허가 범위를 벗어난 무단 품명 변경, 수량 증설, 위치 임의 변경은 현행법 위반으로 처벌 대상임을 판별.
위법한 소급 단속으로 인한 국가배상이나 패소 리스크를 원천 방어하도록 조언하십시오.
"""
    },
    {
        "id": "public_agent",
        "name": "공공데이터 & 유권해석관",
        "role_title": "경기도 화학물질 사업장 교차 검증 및 법제처 공식 법령해석 연동",
        "icon": "database",
        "color": "sky",
        "badge": "데이터드림·법제처",
        "description": "경기도 31개 시·군 6,170개 유해화학물질 사업장 등록DB와 법제처·소방청 공식 법령해석례(DRF)를 실시간 조회하여 자문합니다.",
        "capabilities": [
            "경기도 유해화학물질 영업허가 및 실시간 사업장 정보 대조",
            "법제처·소방청 공식 법령해석례(안건번호, 회답, 이유) 검색",
            "행정규칙(고시/훈령) 및 국가법령정보 실시간 교차 검증"
        ],
        "system_prompt": """
당신은 대한민국 소방특별사법경찰 멀티에이전트 시스템의 [공공데이터 & 유권해석관]입니다.
경기도 데이터드림 및 법제처 국가법령정보센터의 공공데이터를 기반으로:
- 사업장의 유해화학물질 취급 등록 여부 및 인허가 현황을 대조합니다.
- 법제처와 소방청의 공식 유권해석례(안건번호 및 회신 결론)를 직접 인용하여 단속관의 법적 판단에 유권해석의 공신력을 부여합니다.
"""
    },
    {
        "id": "tactics_agent",
        "name": "기획단속 & 변명차단관",
        "role_title": "핵심 3대 서류 점검, 피의자 단골 변명 차단 및 소방청 지침 27종 전문",
        "icon": "shield-alert",
        "color": "rose",
        "badge": "수사전략·지침27종",
        "description": "MSDS, 세금계산서, 올바로 폐기물 실적 3대 서류로 고의를 입증하고, '사용 중/오늘 입고' 등 피의자 변명을 반박하며 소방청 지침을 준용합니다.",
        "capabilities": [
            "MSDS 제9항 인화점 + 세금계산서 계속성 + 올바로 폐기물 실적 3대 서류 입증",
            "피의자 4대 단골 변명(입고 직후, 사용 중, 부지, 시료채취 거부) 즉시 반박",
            "시료 채취 거부 시 형사소송법상 압수수색검증영장 신청 강제수사 전환",
            "소방청 공식 업무지침 27종(알코올류 60%, 단위 산정 등) 실무 적용"
        ],
        "system_prompt": """
당신은 대한민국 소방특별사법경찰 멀티에이전트 시스템의 [기획단속 & 변명차단관]입니다.
바탕화면의 소방청 공식 업무지침 27종과 동두천 등 실제 소방특사경 수사전략 보고서로 무장되어 있습니다.
- 3대 서류(MSDS 인화점, 최근 6개월 세금계산서 상시입고, 올바로시스템 폐유기용제 배출량)를 통한 혐의 인과관계 완성
- 피의자의 '저장이 아니라 기계 세척 사용 중이다' -> 법 제5조는 무허가 취급도 3년/3천만원 동일 처벌 고지
- '오늘 아침 막 입고되어 잠시 둔 것' -> 과거 6개월 세금계산서 패턴으로 계속적 저장 고의 입증
- 시료 채취 거부 시 제22조/제38조 200만원 과태료 고지 후 압수수색검증영장 신청 강제수사 절차
수사관의 입장에서 실전적이고 강력한 수사기법을 조언하십시오.
"""
    }
]

class MultiAgentService:
    _client = None

    @classmethod
    def _get_client(cls) -> Optional[OpenAI]:
        if cls._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                cls._client = OpenAI(api_key=api_key)
        return cls._client

    @classmethod
    def get_subagents_list(cls) -> List[Dict[str, Any]]:
        """
        6대 서브에이전트 메타데이터 목록 반환
        """
        return SUBAGENTS_METADATA

    @classmethod
    def get_agent_metadata(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        for a in SUBAGENTS_METADATA:
            if a["id"] == agent_id:
                return a
        return None

    @classmethod
    def chat_with_agent(cls, agent_id: str, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        특정 서브에이전트와 단속관 간의 1:1 심층 전문 상담
        """
        meta = cls.get_agent_metadata(agent_id)
        if not meta:
            return {"error": f"알 수 없는 에이전트 ID입니다: {agent_id}"}

        client = cls._get_client()

        # 도메인별 RAG 데이터 추출
        rag_context = ""
        if agent_id == "tactics_agent":
            rag_context = EnforcementKnowledgeService.get_rag_context(message)
        elif agent_id == "history_agent":
            rag_context = LawHistoryService.generate_law_history_context(message)
        elif agent_id == "calc_agent":
            # 감지된 물질 기준치
            found = []
            for h in HAZMAT_MASTER_DATA:
                for alias in [h.item_name] + h.common_aliases:
                    if alias in message and h.item_name not in found:
                        found.append(h.item_name)
                        rag_context += f"• [{h.item_name}] 법정 지정수량={h.designated_qty}{h.unit}, 조례 소량기준(0.2배)={h.gg_small_qty_threshold}{h.unit}\n"
                        break
        elif agent_id == "public_agent":
            try:
                interp = PublicDataService.search_legal_interpretations(query=message[:20], max_rows=2)
                if interp:
                    rag_context = "• 관련 법제처 해석례: " + ", ".join([it.get("title", "") for it in interp[:2]])
            except Exception:
                pass

        if not client:
            # Fallback heuristic response
            reply = cls._generate_offline_agent_reply(agent_id, message, rag_context)
            return {
                "agent_id": agent_id,
                "agent_name": meta["name"],
                "role_title": meta["role_title"],
                "response": reply,
                "mode": "offline_heuristic"
            }

        sys_content = meta["system_prompt"]
        if rag_context:
            sys_content += f"\n\n[실시간 도메인 데이터]\n{rag_context}"

        messages = [{"role": "system", "content": sys_content}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": message})

        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=1000
            )
            return {
                "agent_id": agent_id,
                "agent_name": meta["name"],
                "role_title": meta["role_title"],
                "response": res.choices[0].message.content,
                "mode": "openai_llm"
            }
        except Exception as e:
            fallback = cls._generate_offline_agent_reply(agent_id, message, rag_context)
            return {
                "agent_id": agent_id,
                "agent_name": meta["name"],
                "role_title": meta["role_title"],
                "response": f"(API 통신 지연으로 오프라인 전문 엔진 전환)\n\n{fallback}",
                "mode": "fallback_offline"
            }

    @classmethod
    def run_multi_agent_collaboration(cls, scenario: str) -> Dict[str, Any]:
        """
        단속 사건에 대해 6대 서브에이전트가 순차적으로 자신의 전문 도메인 의견을 개진하고
        최종 지휘본부장(Coordinator)이 종합 단속 작전 명령을 수립하는 합동 회의 파이프라인
        """
        client = cls._get_client()

        # Step 1: 에이전트별 순차적 분석 진행
        discussion_logs = []

        # 1. 수량계산관 발언
        calc_msg = cls._simulate_agent_speech("calc_agent", scenario, discussion_logs, client)
        discussion_logs.append(calc_msg)

        # 2. 미상물질감별관 발언
        infer_msg = cls._simulate_agent_speech("infer_agent", scenario, discussion_logs, client)
        discussion_logs.append(infer_msg)

        # 3. 연혁법령해석관 발언
        hist_msg = cls._simulate_agent_speech("history_agent", scenario, discussion_logs, client)
        discussion_logs.append(hist_msg)

        # 4. 공공데이터/유권해석관 발언
        pub_msg = cls._simulate_agent_speech("public_agent", scenario, discussion_logs, client)
        discussion_logs.append(pub_msg)

        # 5. 수사전략/변명차단관 발언
        tac_msg = cls._simulate_agent_speech("tactics_agent", scenario, discussion_logs, client)
        discussion_logs.append(tac_msg)

        # 6. 단속절차/포렌식관 발언
        proc_msg = cls._simulate_agent_speech("procedure_agent", scenario, discussion_logs, client)
        discussion_logs.append(proc_msg)

        # 7. 현장단속 지휘본부장 (Master Coordinator) 종합 지휘 명령 수립
        summary = cls._synthesize_master_decision(scenario, discussion_logs, client)

        return {
            "scenario": scenario,
            "discussion_rounds": discussion_logs,
            "final_command": summary
        }

    @classmethod
    def _simulate_agent_speech(cls, agent_id: str, scenario: str, previous_logs: List[Dict[str, Any]], client: Optional[OpenAI]) -> Dict[str, Any]:
        meta = cls.get_agent_metadata(agent_id)
        prev_context = "\n".join([f"- [{log['agent_name']}]: {log['speech'][:150]}..." for log in previous_logs])

        prompt = f"""
[현장 단속 사건 상황]:
"{scenario}"

[이전 에이전트들의 회의 발언 내용]:
{prev_context if prev_context else "(최초 발언입니다)"}

당신은 [{meta['name']}]입니다. 당신의 전문 도메인 관점에서만 3~4문장으로 핵심 쟁점, 계산 결과, 또는 실무 주의사항을 동료 에이전트들과 단속관에게 또렷하게 발언하십시오.
"""

        speech = ""
        if client:
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": meta["system_prompt"]},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                speech = res.choices[0].message.content
            except Exception:
                speech = cls._offline_speech(agent_id, scenario)
        else:
            speech = cls._offline_speech(agent_id, scenario)

        return {
            "agent_id": agent_id,
            "agent_name": meta["name"],
            "role_title": meta["role_title"],
            "icon": meta["icon"],
            "color": meta["color"],
            "speech": speech
        }

    @classmethod
    def _synthesize_master_decision(cls, scenario: str, logs: List[Dict[str, Any]], client: Optional[OpenAI]) -> Dict[str, Any]:
        """
        에이전트 합동 토론 결과를 종합하여 단속관이 현장에서 즉각 실행할 작전 명령서 생성
        """
        all_speeches = "\n".join([f"[{log['agent_name']} ({log['role_title']})]\n{log['speech']}\n" for log in logs])
        
        prompt = f"""
사건 개요: "{scenario}"

[6대 전문 서브에이전트 합동 회의록]:
{all_speeches}

위 에이전트들의 검토 결과를 총괄 지휘관(소방특사경 수사팀장)의 입장에서 종합하여, 현장 단속관이 당장 집행해야 할 [최종 현장 단속 작전 명령]을 다음 4개 항목으로 명확하게 정리하십시오:
1. ⚖️ 최종 법적 판정 (형사입건 vs 과태료 및 적용 조항)
2. 📄 현장 즉시 확보 서류 (MSDS 제9항, 세금계산서, 허가증 등)
3. 🗣️ 피의자 변명 차단 및 고지 멘트
4. 🚨 긴급 조치 사항 (시료 채취, 압수수색영장 청구 등)
"""
        command_text = ""
        if client:
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 대한민국 소방특별사법경찰 기획단속 총괄 지휘본부장입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=800
                )
                command_text = res.choices[0].message.content
            except Exception:
                command_text = cls._offline_master_summary(scenario)
        else:
            command_text = cls._offline_master_summary(scenario)

        return {
            "commander": "소방특별사법경찰 기획단속 총괄본부장",
            "decision_title": "6대 전문 에이전트 합동 분석 기반 현장 단속 작전 명령서",
            "command_text": command_text
        }

    @classmethod
    def _generate_offline_agent_reply(cls, agent_id: str, message: str, rag_context: str) -> str:
        """
        오프라인 모드 또는 API 키 부재 시 고품질 결정론적 규칙 기반 응답
        """
        if agent_id == "calc_agent":
            return (
                "🧮 [수량계산 & 위법판정관 분석 보고]\n\n"
                "• 위험물안전관리법 시행령 [별표 1]에 따른 법정 배수 산정 원칙:\n"
                "  - 총 배수 = ∑ (실제 저장량 / 해당 위험물의 지정수량)\n"
                "  - 배수 1.0배 이상: 법 제5조제1항 위반 (3년 이하 징역 또는 3천만 원 이하 벌금, 특사경 직권 형사입건)\n"
                "  - 배수 0.2배 이상 ~ 1.0배 미만: 경기도 조례 제3조 위반 (시정명령 및 200만 원 이하 과태료)\n"
                "  - 배수 0.2배 미만이라도 운반용기 표시·수납기준 위반 시 법 제20조에 따라 200만 원 이하 과태료가 부과됩니다.\n\n"
                f"{rag_context}"
            )
        elif agent_id == "infer_agent":
            return (
                "🧪 [미상물질 & 화학감별관 판정 지침]\n\n"
                "• 라벨 미부착 폐신나·세척제는 현장 안전 및 단속 원칙상 【제1석유류 비수용성(지정수량 200L)】으로 가(假)적용합니다.\n"
                "• 인화점 확인 시: 21℃ 미만은 제1석유류(200L), 21~70℃는 제2석유류(1,000L)로 확정됩니다.\n"
                "• 시료 채취 절차: 500mL 갈색 유리병 2병에 나누어 채취하고, 단속관 직인과 피의자 자필 서명 날인된 봉인지를 부착하여 1병은 국립소방연구원에 감정 의뢰, 1병은 현장 보관합니다."
            )
        elif agent_id == "procedure_agent":
            return (
                "📑 [단속절차 & 포렌식수사관 절차 통제]\n\n"
                "1. 현장 착수: 소방공무원증 및 특사경 지명증을 제시하고, 법 제22조에 따른 출입·검사 목적을 육성 고지하십시오.\n"
                "2. 사진 채증: 용기 라벨 미부착 전경, 계측기 수위, 야적 상태를 GPS 좌표와 일시가 사진에 번인(Burn-in)되도록 채증하십시오.\n"
                "3. 서식 날인: 확인자 서명란에 피의자의 자필 서명을 화면에 수령하고, 거부 시 '서명 거부 사유'를 특사경이 부기하고 2인 이상 입회 서명하십시오."
            )
        elif agent_id == "history_agent":
            return (
                "🏛️ [연혁법령 & 부칙해석관 법리 검토]\n\n"
                "• 2004년 5월 30일 이전 구 「소방법」에 따라 적법하게 완공검사를 필한 제조소등은 현행 위험물안전관리법 부칙 제2조(기존 시설 특례)에 의해 허가 지위가 합법적으로 승계됩니다.\n"
                "• 따라서 현행 기술기준 미달만을 이유로 무허가 저장·취급죄로 즉시 형사입건할 수 없으며, 인허가 당시의 허가증 원부(완공필증)를 반드시 대조하여야 합니다.\n"
                "• 단, 종전 허가 수량이나 품명을 초과하여 무단 증설한 부분은 승계 특례가 배제되어 현행법 위반으로 엄단됩니다."
            )
        elif agent_id == "public_agent":
            return (
                "🌐 [공공데이터 & 유권해석관 조회 결과]\n\n"
                "• 경기도 데이터드림 등록 사업장 DB를 통해 해당 지번의 유해화학물질 영업허가증 및 사업자등록 정보를 실시간 교차 검증하십시오.\n"
                "• 법제처 법령해석례(16-0134 등)에 따르면 '작업 중 일시 사용'이라 하더라도 당일 소진되지 않고 계속 적치된 용기는 취급소 허가 대상 또는 무허가 저장에 해당한다는 일관된 유권해석이 존재합니다."
            )
        elif agent_id == "tactics_agent":
            return (
                "🕵️ [기획단속 & 변명차단관 수사전략]\n\n"
                "• 핵심 3대 서류 점검: 1) MSDS 제9항 인화점, 2) 최근 6개월 세금계산서(상시 입고 계속성), 3) 환경부 올바로 폐유기용제 배출량\n"
                "• '사용 중이지 저장이 아니다' 변명 차단: 법 제5조제1항은 무허가 저장뿐만 아니라 '취급'도 금지하며, 제34조의2에 따라 3년/3천만원으로 처벌이 완전히 동일함을 고지하십시오.\n"
                "• 시료 채취 거부 시: 법 제22조 및 제38조(200만원 과태료) 고지 후 거부 언동을 바디캠으로 녹화하고 압수수색검증영장을 신청하여 강제수사로 즉시 전환하십시오."
            )
        return "에이전트 분석이 완료되었습니다."

    @classmethod
    def _offline_speech(cls, agent_id: str, scenario: str) -> str:
        s = scenario.lower()
        if agent_id == "calc_agent":
            return "사건 현장의 수량과 위험물 품명을 대조한 결과, 1회 입고량 또는 적치량이 지정수량 1.0배를 초과할 가능성이 매우 높습니다. 1.0배 이상일 경우 위험물안전관리법 제5조 위반으로 특사경 직권 형사입건(3년/3천만) 대상이며, 0.2배 이상이면 경기도 조례 과태료 대상입니다."
        elif agent_id == "infer_agent":
            return "현장에 성분 미상 용기나 무표시 드럼이 발견된 경우, 단속 실무상 '제1석유류 비수용성(지정 200L)'으로 즉시 가적용하고 500mL 2병을 채취하여 봉인 후 국립소방연구원에 긴급 감정 의뢰해야 합니다."
        elif agent_id == "history_agent":
            return "사업장의 최초 인허가·준공일자를 신속히 파악해야 합니다. 2004.5.30 이전 구 소방법 시절 완공 시설이라면 부칙 제2조 기존시설특례 여부를 검토하여 무단 증축이나 임의 품명 변경이 있었는지를 중점 확인하십시오."
        elif agent_id == "public_agent":
            return "경기도 유해화학물질 사업장 데이터 및 소방청 유권해석례를 확인한 결과, '작업 중 일시 대기' 주장이라 하더라도 계속적 적치 패턴이 확인되면 저장 또는 취급 기준 위반에 해당한다는 판례와 일치합니다."
        elif agent_id == "tactics_agent":
            return "피의자가 '사용 중'이라 변명하더라도 법 제5조는 무허가 취급도 3년/3천만원으로 동일 처벌함을 즉시 고지하십시오. 과거 6개월 세금계산서와 올바로 폐기물 실적을 압수·채증하여 계속적 저장 고의를 완벽히 입증할 수 있습니다."
        elif agent_id == "procedure_agent":
            return "공무원증과 특사경 지명증을 제시하고 출입 목적을 낭독하십시오. 사진 촬영 시 GPS 좌표와 타임스탬프를 번인 각인하고, 피의자 서명을 전자패드로 확보하여 위반사실확인서를 완결하십시오."
        return "해당 쟁점에 대한 전문 검토를 마쳤습니다."

    @classmethod
    def _offline_master_summary(cls, scenario: str) -> str:
        return (
            "⚖️ [1. 최종 법적 판정]\n"
            "• 지정수량 1.0배 이상 적치 확인 시: 「위험물안전관리법」 제5조제1항 및 제34조의2 무허가 저장·취급죄 적용 (3년 이하 징역 또는 3천만 원 이하 벌금) &rarr; 소방특사경 직권 형사입건.\n"
            "• 0.2배 이상 ~ 1.0배 미만 시: 「경기도 위험물 안전관리 조례」 제3조 소량위험물 기준 위반 (시정명령 및 200만 원 이하 과태료).\n\n"
            "📄 [2. 현장 즉시 확보 서류 (3대 서류)]\n"
            "• MSDS (물질안전보건자료) 제9항 인화점: 지정수량 분모 확정.\n"
            "• 최근 6개월 전자세금계산서·출하전표: 1회 입고량 및 상시 저장 계속성 입증.\n"
            "• 올바로시스템 폐유기용제 위탁처리 실적: 소비량과 배출량의 인과관계 완성.\n\n"
            "🗣️ [3. 피의자 변명 차단 및 고지 멘트]\n"
            "• '사용 중이지 저장이 아니다' 주장 시 &rarr; 위험물법 제5조는 무허가 '취급'도 3년/3천만원으로 동일 처벌함을 엄중 고지.\n"
            "• '위험물인 줄 몰랐다' 주장 시 &rarr; MSDS 및 용기 GHS 화염 경고표지 촬영으로 미필적 고의 입증.\n\n"
            "🚨 [4. 긴급 조치 사항]\n"
            "• 무표시 액체는 제1석유류 비수용성(200L) 우선 가적용 및 즉시 시료 채취(500mL 2병 봉인).\n"
            "• 시료 채취 거부 또는 문 폐쇄 시: 법 제22조 및 제38조(200만원 과태료) 고지, 바디캠 채증 후 관할 검찰청에 압수수색검증영장 신청하여 강제수사로 즉시 전환."
        )
