"""
services/enforcement_knowledge_service.py
바탕화면 '위험물 기획단속 ai' 폴더 내 48개 단속 매뉴얼, 소방청 공식 업무지침,
질의회신집, 실무해설서, 수사전략 지식 베이스 검색 및 RAG 엔진
"""
import os
import re
import json
from typing import List, Dict, Any, Optional

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "enforcement_knowledge.json")

class EnforcementKnowledgeService:
    _knowledge_cache: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def _load_kb(cls) -> List[Dict[str, Any]]:
        if cls._knowledge_cache is not None:
            return cls._knowledge_cache

        if not os.path.exists(KB_PATH):
            return []

        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                cls._knowledge_cache = json.load(f)
        except Exception as e:
            print(f"[KnowledgeService] Failed to load KB: {e}")
            cls._knowledge_cache = []

        return cls._knowledge_cache

    @classmethod
    def get_investigation_tactics(cls) -> Dict[str, Any]:
        """
        동두천 등 소방특사경 기획단속 수사전략 보고서 기반 핵심 3대 서류 및 피의자 변명 차단 매뉴얼
        """
        return {
            "title": "소방특별사법경찰 무허가 위험물 기획단속 핵심 수사기법",
            "three_key_documents": [
                {
                    "name": "MSDS (물질안전보건자료)",
                    "purpose": "위험물 해당 여부(인화점, 성분) 및 지정수량(분모) 확정",
                    "legal_ground": "산업안전보건법 제114조 (미비치 시 과태료 최대 500만원 회피 목적 비치)",
                    "action_tip": "제9항 물리화학적 특성 중 '인화점(Flash Point)' 필수 확인. 21℃ 미만(제1석유류 비수용성 200L), 21~70℃(제2석유류 1,000L) 특정하여 '자백 증거'로 채증."
                },
                {
                    "name": "최근 6개월~1년 치 전자세금계산서 / 거래명세표",
                    "purpose": "1회 입고량, 구매 주기, 상시 저장량 및 계속성(반복성) 입증",
                    "legal_ground": "단순 일시 보관 주장의 탄핵 및 상시 무허가 저장 입증",
                    "action_tip": "1회 납품량이 지정수량 이상(예: 신나 3드럼=600L)인 경우 입고 당일 무허가 저장 완료 입증. 거래처(화공약품상) 납품내역 대조."
                },
                {
                    "name": "폐기물 위탁처리 실적 보고서 (환경부 올바로시스템)",
                    "purpose": "위험물의 실제 공정 투입·소비 및 배출 사실 교차 입증",
                    "legal_ground": "폐기물관리법상 폐유기용제(폐신나 등) 배출자 신고 내역",
                    "action_tip": "구매량 ≈ 제품소비량 + 폐유기용제 배출량 + 현장 재고의 인과관계 완성으로 '사용 안 했다', '다른 곳에 썼다'는 변명 원천 차단."
                }
            ],
            "suspect_defense_countermeasures": [
                {
                    "excuse": "오늘 아침에 막 입고되어 잠시 둔 것일 뿐, 저장이 아닙니다.",
                    "countermeasure": "과거 6개월 치 세금계산서와 출하증명서를 제시하여 수개월 전부터 주 1~2회씩 3~4드럼씩 지속적으로 입고·적치된 패턴을 제시하여 계속적 무허가 저장 고의 자백 유도."
                },
                {
                    "excuse": "지금 기계 세척에 작업 중으로 사용하고 있는 것이지 보관·저장하는 게 아닙니다.",
                    "countermeasure": "위험물안전관리법 제5조제1항은 '저장'뿐만 아니라 무허가 '취급'도 동일하게 금지하며, 제34조의2에 따라 3년 이하 징역 또는 3천만원 이하 벌금으로 처벌 수위가 동일함을 고지."
                },
                {
                    "excuse": "이 물질이 위험물안전관리법상 위험물인 줄 전혀 몰랐습니다.",
                    "countermeasure": "사업장 내 비치된 MSDS 제9항(인화점)과 드럼/말통에 부착된 GHS 인화성 경고표지(화염 마크) 사진을 채증하여 제시함으로써 미필적 고의 및 안전주의의무 위반 입증."
                },
                {
                    "excuse": "시료 채취(수거)를 거부하며 문을 닫고 들어가지 못하게 합니다.",
                    "countermeasure": "위험물안전관리법 제22조(출입·검사) 및 제38조(출입·수거 거부 시 200만원 과태료)를 낭독하고, 거부 언동을 바디캠/영상으로 채증한 뒤 즉시 관할 검찰청에 형사소송법상 압수수색검증영장 신청하여 강제수사로 전환."
                }
            ],
            "ordinance_two_track": {
                "rule": "1.0배 이상은 형사입건(특사경), 0.2배~1.0배 미만은 경기도 조례 과태료 및 시정명령",
                "ordinance_standards": [
                    "벽·바닥·보·지붕 불연재료 구조",
                    "0.1m 이상 턱(방유턱) 또는 집유설비 설치",
                    "외부 환기 및 가연성 유증기 배출설비",
                    "용기 경고표지(품명, 수량, 화기엄금) 부착",
                    "능력단위 3단위 이상 소화기 1대 이상 비치"
                ]
            }
        }

    @classmethod
    def search_knowledge(cls, query: str = "", category: str = "all", limit: int = 20) -> List[Dict[str, Any]]:
        """
        48개 학습 문서 대상 키워드 검색
        """
        kb = cls._load_kb()
        if not kb:
            return []

        q = (query or "").strip().lower()
        results = []

        for item in kb:
            if category != "all" and item.get("category") != category:
                continue

            fname = item.get("filename", "").lower()
            content = item.get("content", "").lower()

            if not q:
                # 검색어 없으면 전체 목록 요약
                results.append({
                    "id": item["id"],
                    "filename": item["filename"],
                    "category": item["category"],
                    "size_kb": item["size_kb"],
                    "char_count": item["char_count"],
                    "snippet": item["summary_preview"]
                })
                continue

            # 검색어 매칭
            keywords = q.split()
            matched = all(kw in fname or kw in content for kw in keywords)

            if matched:
                # 스니펫 생성
                snippet = ""
                pos = content.find(keywords[0])
                if pos != -1:
                    start = max(0, pos - 80)
                    end = min(len(item["content"]), pos + 220)
                    snippet = "..." + item["content"][start:end].replace("\n", " ") + "..."
                else:
                    snippet = item["summary_preview"]

                results.append({
                    "id": item["id"],
                    "filename": item["filename"],
                    "category": item["category"],
                    "size_kb": item["size_kb"],
                    "char_count": item["char_count"],
                    "snippet": snippet
                })

        return results[:limit]

    @classmethod
    def get_document_content(cls, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        특정 문서 ID의 전문 조회
        """
        kb = cls._load_kb()
        for item in kb:
            if item.get("id") == doc_id:
                return item
        return None

    @classmethod
    def get_rag_context(cls, user_message: str) -> str:
        """
        AI 챗봇 질의 시 질문에서 핵심 위험물 단속 쟁점을 감지하여
        48개 학습 매뉴얼/소방청 지침/수사전략에서 가장 관련도 높은 지식 청크를 프롬프트에 주입
        """
        kb = cls._load_kb()
        if not kb:
            return ""

        msg = user_message.lower()
        matched_chunks = []

        # 1. 수사 전략 키워드 감지
        if any(k in msg for k in ["단속", "적발", "수사", "변명", "고의", "입증", "세금계산서", "msds", "올바로", "시료", "채취", "영장", "거부"]):
            tactics = cls.get_investigation_tactics()
            t_text = (
                "[소방특사경 현장 기획단속 수사전략 매뉴얼 RAG]\n"
                "• 혐의 입증 핵심 3대 서류: 1) MSDS 제9항 인화점(분모 확정), 2) 세금계산서(상시 저장 계속성 입증), 3) 올바로 폐기물 배출량(인과관계 완성)\n"
                "• 피의자 단골 변명 차단: '오늘 막 입고' -> 과거 6개월 세금계산서 제시, '사용 중' -> 법 제5조 무허가 취급도 3년/3천만원 동일 처벌, '몰랐다' -> MSDS 및 용기 GHS 표지로 미필적 고의 입증\n"
                "• 시료 채취 거부 시: 법 제22조 및 제38조(200만원 과태료) 고지, 거부 영상 채증 후 압수수색검증영장 신청 강제수사 전환\n"
            )
            matched_chunks.append(t_text)

        # 2. 옥내저장소 보유공지 및 무단 증축·컨테이너 설치 관련 핵심 법리 주입
        if any(k in msg for k in ["보유공지", "공지", "옥내저장소", "컨테이너", "복도", "구조물", "가설", "거리", "떨어", "증축", "변경허가", "변경신고"]):
            holding_space_text = (
                "[위험물 옥내저장소 보유공지 및 무단 구조변경 법적 기준]\n"
                "• 보유공지 확보 의무 (구 소방법 시행규칙 [별표 17], 현행 위험물안전관리법 시행규칙 [별표 5]):\n"
                "  - 옥내저장소 외벽 주위에는 화재 시 연소 확대 방지 및 소화활동 공간 확보를 위해 배수별 보유공지(지정수량 5배 이하 0.5m 이상, 5~10배 1m 이상, 10~20배 2m 이상, 20~50배 3m 이상, 50~200배 5m 이상)를 필수적으로 유지해야 함.\n"
                "  - ★공지 내 물건 적치 및 공작물 설치 절대 금지: 보유공지는 화재안전상 절대적인 공지로서, 공지 내에 컨테이너박스(가설건축물), 복도 구조물, 차양, 계단, 파이프랙, 자재 적치 등을 하는 것은 '보유공지 침범 및 소멸'로서 위험물안전관리법 제5조제3항(기술기준 위반)에 명백히 위반됨.\n"
                "• 독립된 전용 건축물 요건:\n"
                "  - 옥내저장소는 원칙적으로 독립된 단층 건물이어야 하며, 상부에 복도 구조물이 지나가거나 다른 건축물과 연결통로로 연결되는 경우 연소확대 위험 및 독립성 요건 위반임.\n"
                "• 변경허가 미필죄 (법 제6조제1항, 제36조제1호):\n"
                "  - 완공검사필증 허가 도면에 없던 컨테이너박스나 복도 구조물을 소방서장의 사전 변경허가 없이 무단 설치·증축한 행위는 1년 이하의 징역 또는 1천만 원 이하의 벌금 (형사처벌 대상)임.\n"
                "• 부칙 제2조(기존시설 특례) 승계 배제:\n"
                "  - 2004.5.30 이전 구 소방법 시절 허가받은 시설이라 하더라도, 완공 이후 무단 설치·증축된 구조물은 기존 허가 범위를 벗어난 불법 개조이므로 부칙 특례의 보호를 전혀 받지 못하고 현행법 위반으로 엄단됨.\n"
            )
            matched_chunks.append(holding_space_text)

        # 3. 소방청 지침 및 질의회신 관련 키워드 감지
        triggers = [
            ("알코올", ["알코올류의 판정기준"]),
            ("수용성", ["수용성의 인화성 액체"]),
            ("단위", ["제조소등의단위및저장취급량산정"]),
            ("저장취급량", ["제조소등의단위및저장취급량산정"]),
            ("품명", ["품명․수량 또는 지정수량배수의 변경신고"]),
            ("변경신고", ["품명․수량 또는 지정수량배수의 변경신고"]),
            ("주유", ["주유취급소"]),
            ("안전관리자", ["안전관리자"]),
            ("정기점검", ["정기점검"]),
            ("휴지", ["휴지"]),
            ("사용중지", ["사용중지"]),
            ("조례", ["경기도 위험물 안전관리 조례"]),
            ("소량위험물", ["경기도 위험물 안전관리 조례"]),
            ("이동탱크", ["이동탱크저장소"]),
            ("변압기", ["변압기"]),
            ("voc", ["휘발성유기화합물"])
        ]

        relevant_docs = []
        for kw, target_names in triggers:
            if kw in msg:
                for doc in kb:
                    for tn in target_names:
                        if tn in doc["filename"]:
                            if doc["id"] not in [d["id"] for d in relevant_docs]:
                                relevant_docs.append(doc)

        for doc in relevant_docs[:3]:
            # 핵심 텍스트 요약 (최대 1000자)
            snippet = doc["content"][:1000].replace("\n\n", "\n")
            matched_chunks.append(f"[소방청 공식 지침/자료: {doc['filename']}]\n{snippet}")

        if not matched_chunks:
            # 기본 실무 원칙 주입
            matched_chunks.append(
                "[위험물안전관리법 및 소방특사경 핵심 단속 원칙]\n"
                "• 지정수량 1.0배 이상 무허가 저장·취급: 3년 이하 징역 또는 3천만원 이하 벌금 (형사입건)\n"
                "• 지정수량 0.2배 이상 ~ 1.0배 미만: 경기도 조례 소량위험물 기준 위반 시정명령 및 200만원 이하 과태료\n"
                "• 운반용기 표시·수납기준 위반 (법 제20조): 지정수량 미만이라도 전국 공통 200만원 이하 과태료 부과\n"
            )

        return "\n\n".join(matched_chunks)
