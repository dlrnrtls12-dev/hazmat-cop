"""
services/law_history_service.py
법제처 국가법령정보센터 DRF API 기반 연혁법령(eflaw) 및 행정규칙(admrul) 연혁 엔진
- 위험물안전관리법, 시행령, 시행규칙, 행정규칙(고시/훈령)의 전체 제·개정 연혁 추적
- 과거 시점(건물 인허가일, 사용승인일, 시설 설치일) 기준 당시 시행본 및 부칙 경과조치(기존시설 특례) 실시간 조회
"""
import os
import re
import datetime as dt
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any
import requests
from dotenv import load_dotenv

load_dotenv()

class LawHistoryService:
    SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
    BODY_URL = "https://www.law.go.kr/DRF/lawService.do"
    OFFICIAL_URL = "https://www.law.go.kr"
    OC_KEY = os.getenv("LAW_API_ID", "lgs9941")

    # 1. 연혁 법령 및 행정규칙 목록 검색
    @classmethod
    def search_law_history(
        cls,
        query: str = "위험물안전관리법",
        as_of: Optional[str] = None,
        target: str = "eflaw",  # 'eflaw' (연혁법령) 또는 'admrul' (행정규칙)
        mode: str = "all",       # 'all' (현행+연혁 전체), 'current' (현행만), 'history' (연혁만)
        page: int = 1,
        display: int = 20
    ) -> Dict[str, Any]:
        """
        법제처 연혁 법령 검색 API
        - target: 'eflaw' (법률/시행령/시행규칙 연혁), 'admrul' (행정규칙/고시/훈령 연혁)
        - as_of: YYYY-MM-DD 형식의 기준일자 (해당 일자 이전 당시 시행본 필터링)
        """
        # nw 파라미터 매핑 (법제처 공식 규격)
        if target == "eflaw":
            nw_map = {"current": "3", "history": "1", "all": "1,3"}
            nw = nw_map.get(mode, "1,3")
        else:
            nw_map = {"current": "1", "history": "2", "all": "1"}
            nw = nw_map.get(mode, "1")

        params = {
            "OC": cls.OC_KEY,
            "target": target,
            "type": "XML",
            "query": query,
            "nw": nw,
            "search": "1",
            "sort": "efdes",  # 시행일자 최신순 정렬
            "page": str(page),
            "display": str(display)
        }

        # 과거 기준일자가 주어지면 해당 일자 이전 당시 시행본만 필터링
        if as_of:
            clean_date = as_of.replace("-", "").replace(".", "").strip()
            if len(clean_date) == 8 and clean_date.isdigit():
                params["efYd"] = f"19480101~{clean_date}"

        results = {
            "total_count": 0,
            "page": page,
            "as_of": as_of,
            "items": []
        }

        try:
            resp = requests.get(cls.SEARCH_URL, params=params, timeout=6)
            if resp.status_code == 200 and resp.content:
                root = ET.fromstring(resp.content)
                total_cnt = int(root.findtext(".//totalCnt", "0") or "0")
                results["total_count"] = total_cnt

                row_tag = "law" if target == "eflaw" else "admrul"
                for row in root.findall(f".//{row_tag}"):
                    mst = row.findtext("법령일련번호") or row.findtext("행정규칙일련번호") or ""
                    law_name = (row.findtext("법령명한글") or row.findtext("행정규칙명") or "").strip()
                    ef_date_raw = (row.findtext("시행일자") or "").strip()
                    prom_date_raw = (row.findtext("공포일자") or row.findtext("발령일자") or "").strip()
                    prom_no = (row.findtext("공포번호") or row.findtext("발령번호") or "").strip()
                    status = (row.findtext("현행연혁코드") or row.findtext("현행연혁구분") or "").strip()
                    change_type = (row.findtext("제개정구분명") or "").strip()

                    # 날짜 형식 포맷팅 (YYYY-MM-DD)
                    def fmt_date(d_str):
                        if len(d_str) == 8 and d_str.isdigit():
                            return f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:]}"
                        return d_str

                    ef_date = fmt_date(ef_date_raw)
                    prom_date = fmt_date(prom_date_raw)

                    detail_url = ""
                    if target == "eflaw":
                        detail_url = f"{cls.OFFICIAL_URL}/LSW/lsInfoP.do?lsiSeq={mst}&efYd={ef_date_raw}"
                    else:
                        detail_url = f"{cls.OFFICIAL_URL}/LSW/admRulInfoP.do?admRulSeq={mst}"

                    results["items"].append({
                        "target": target,
                        "mst": mst,
                        "law_name": law_name,
                        "effective_date": ef_date,
                        "effective_date_raw": ef_date_raw,
                        "promulgation_date": prom_date,
                        "promulgation_no": prom_no,
                        "status": status,
                        "change_type": change_type,
                        "detail_url": detail_url
                    })
        except Exception as e:
            print(f"[LawHistoryService] Search error: {e}")

        return results

    # 2. 특정 연혁 시행본의 본문, 조문, 부칙(경과조치) 전문 조회
    @classmethod
    def get_law_history_detail(
        cls,
        mst: str,
        effective_date_raw: str = "",
        target: str = "eflaw"
    ) -> Optional[Dict[str, Any]]:
        """
        법제처 연혁 본문 상세 조회 (조문, 부칙, 별표 전문 파싱)
        """
        if target == "eflaw":
            params = {
                "OC": cls.OC_KEY,
                "target": "eflaw",
                "MST": mst,
                "efYd": effective_date_raw.replace("-", "").strip(),
                "type": "XML",
                "chrClsCd": "010202"
            }
        else:
            params = {
                "OC": cls.OC_KEY,
                "target": "admrul",
                "ID": mst,
                "type": "XML"
            }

        try:
            resp = requests.get(cls.BODY_URL, params=params, timeout=8)
            if resp.status_code == 200 and resp.content:
                root = ET.fromstring(resp.content)
                law_name = (root.findtext(".//법령명_한글") or root.findtext(".//법령명한글") or root.findtext(".//행정규칙명") or "").strip()
                ef_date_raw = (root.findtext(".//시행일자") or effective_date_raw).strip()
                prom_date_raw = (root.findtext(".//공포일자") or root.findtext(".//발령일자") or "").strip()
                prom_no = (root.findtext(".//공포번호") or root.findtext(".//발령번호") or "").strip()

                # 1) 본문 조문 추출
                articles = []
                for art in root.findall(".//조문단위"):
                    art_title = (art.findtext("조문제목") or "").strip()
                    art_no = (art.findtext("조문번호") or "").strip()
                    art_content = (art.findtext(".//조문내용") or "").strip()
                    
                    # 항/호 내용 취합
                    sub_contents = []
                    for sub in art.findall(".//항내용"):
                        txt = (sub.text or "").strip()
                        if txt:
                            sub_contents.append(txt)
                    for sub in art.findall(".//호내용"):
                        txt = (sub.text or "").strip()
                        if txt:
                            sub_contents.append("  " + txt)

                    full_text = art_content
                    if sub_contents:
                        full_text += "\n" + "\n".join(sub_contents)

                    articles.append({
                        "number": art_no,
                        "title": art_title,
                        "content": full_text
                    })

                # 2) 부칙(경과조치) 추출 - ★ 단속 실무 핵심!
                addenda = []
                for ad in root.findall(".//부칙단위"):
                    ad_title = (ad.findtext("부칙제목") or "부칙").strip()
                    ad_prom_date = (ad.findtext("부칙공포일자") or "").strip()
                    ad_prom_no = (ad.findtext("부칙공포번호") or "").strip()
                    ad_content = (ad.findtext(".//부칙내용") or "").strip()

                    # 부칙 본문에서 경과조치/기존시설 특례 여부 태깅
                    has_transitional = any(kw in ad_content for kw in ["경과조치", "종전", "기존", "소방법", "제조소", "저장소", "취급소", "적용례", "유예"])

                    addenda.append({
                        "title": ad_title,
                        "prom_date": ad_prom_date,
                        "prom_no": prom_no or ad_prom_no,
                        "content": ad_content,
                        "has_transitional_clause": has_transitional
                    })

                return {
                    "target": target,
                    "mst": mst,
                    "law_name": law_name,
                    "effective_date_raw": ef_date_raw,
                    "promulgation_date_raw": prom_date_raw,
                    "promulgation_no": prom_no,
                    "articles_count": len(articles),
                    "addenda_count": len(addenda),
                    "articles": articles,
                    "addenda": addenda
                }
        except Exception as e:
            print(f"[LawHistoryService] Detail error: {e}")

        return None

    # 3. 특정 일자(예: 1999-05-20) 당시 시행되던 법령본 자동 추적
    @classmethod
    def find_applicable_law_as_of(cls, law_name: str, target_date: str) -> Optional[Dict[str, Any]]:
        """
        특정 일자(건물 인허가일, 사용승인일) 기준 당시 시행 중이던 법령본 1건 자동 탐색
        - 2004-05-30 이전의 경우 구법인 「소방법」 및 2004년 위험물안전관리법 제정 부칙을 연계
        """
        clean_target = target_date.replace("-", "").replace(".", "").strip()
        is_pre_2004 = clean_target < "20040530"

        # 2004년 이전이면 구법인 '소방법' 검색, 2004년 이후면 지정된 law_name 검색
        search_query = "소방법" if (is_pre_2004 and "위험물" in law_name) else law_name
        search_res = cls.search_law_history(query=search_query, as_of=target_date, target="eflaw", mode="all", page=1, display=15)
        items = search_res.get("items", [])

        # target_date 이하인 시행일자 중 가장 최신인 항목 탐색
        candidates = []
        for it in items:
            ef_raw = it.get("effective_date_raw", "")
            if ef_raw and ef_raw <= clean_target:
                candidates.append(it)

        if candidates:
            candidates.sort(key=lambda x: x["effective_date_raw"], reverse=True)
            best = candidates[0]
            detail = cls.get_law_history_detail(best["mst"], best["effective_date_raw"], target="eflaw")
            return {
                "matched_version": best,
                "detail": detail,
                "is_pre_2004": is_pre_2004
            }

        # 만약 구법 매칭이 안되면 2004-05-30 제정 당시 위험물안전관리법 본문 로드
        initial_res = cls.search_law_history(query="위험물안전관리법", as_of="2004-05-30", target="eflaw", mode="all", page=1, display=5)
        initial_items = initial_res.get("items", [])
        if initial_items:
            best = initial_items[0]
            detail = cls.get_law_history_detail(best["mst"], best["effective_date_raw"], target="eflaw")
            return {
                "matched_version": best,
                "detail": detail,
                "is_pre_2004": is_pre_2004
            }

        return None

    # 4. 연혁 법령 RAG 컨텍스트 생성 (AI 챗봇 질의 시 주입용)
    @classmethod
    def generate_law_history_context(cls, user_message: str) -> str:
        """
        사용자 질문에서 과거 시점(연도, 날짜, 소방법 시절, 기존 시설 등)을 감지하고,
        해당 시점 당시의 위험물안전관리법 및 부칙 경과조치를 자동으로 요약하여 챗봇용 컨텍스트로 반환
        """
        year_match = re.search(r"(19\d{2}|20[0-2]\d)\s*년?", user_message)
        date_match = re.search(r"(19\d{2}|20[0-2]\d)[-./](0[1-9]|1[0-2])[-./](0[1-9]|[12]\d|3[01])", user_message)
        has_history_kw = any(kw in user_message for kw in ["연혁", "경과조치", "종전", "소방법 시절", "구법", "당시", "기존 시설", "완공일", "인허가일", "사용승인", "옛날"])

        if not year_match and not date_match and not has_history_kw:
            return ""

        # 기준 날짜 산출
        target_date = "2004-05-30"
        if date_match:
            target_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        elif year_match:
            target_date = f"{year_match.group(1)}-06-30"

        applicable = cls.find_applicable_law_as_of("위험물안전관리법", target_date)
        if not applicable or not applicable.get("detail"):
            return ""

        detail = applicable["detail"]
        matched_ver = applicable["matched_version"]
        is_pre_2004 = applicable.get("is_pre_2004", False)

        # 부칙 및 경과조치 추출
        transitional_snippets = []
        for ad in detail.get("addenda", []):
            ad_content = ad.get("content", "")
            if ad.get("has_transitional_clause") or "경과조치" in ad_content or "종전" in ad_content:
                lines = ad_content.split("\n")
                filtered = [l.strip() for l in lines if l.strip() and any(k in l for k in ["경과조치", "종전", "소방법", "제조소", "기존", "유예", "제1조", "제2조", "제3조"])]
                if filtered:
                    transitional_snippets.append("\n".join(filtered[:8]))

        summary_txt = f"""
[법제처 공식 연혁법령 및 부칙 경과조치 RAG 연계]
■ 조회 기준 시점: {target_date} (질문에서 감지된 과거 시점)
■ 당시 적용 법령본: {matched_ver.get('law_name')} [시행 {matched_ver.get('effective_date')}] (공포 제{matched_ver.get('promulgation_no')}호)
■ 핵심 법리 원칙 (단속관 판단 가이드):
  1) 행위시법 적용 원칙: 위험물 제조소등의 시설 기준(방유제, 보유공지, 내화구조 등)은 원칙적으로 '시설 설치 허가 또는 완공 당시의 법령'을 기준으로 판단함.
  2) 기존 시설 특례 및 경과조치 (★핵심):
     - 2004.5.30 위험물안전관리법 제정 이전 종전 「소방법」에 따라 적법하게 허가·승인받아 설치된 시설은 위험물안전관리법 부칙 제2조에 따라 이 법에 의한 제조소등으로 승계·인정됨.
     - 법령 개정으로 기술기준이 강화되더라도 부칙에 '기존 시설에 대한 경과조치' 또는 '유예기간'이 규정되어 있다면, 단순 시설미비만으로 즉시 무허가 형사처벌을 할 수 없으며 보완 명령 대상인지 검토해야 함.
  3) 소급 적용 및 예외: 화재 예방상 중대한 위험이 있어 개정 법령에서 명시적으로 기존 시설에 소급 적용하도록 정한 사항(예: 특정 소화설비 보강 등)이나, 무허가 증축·위치변경·품명변경 등 인허가 범위를 초과한 행위는 현행법 위반으로 엄정 처벌됨.
"""
        if transitional_snippets:
            summary_txt += "\n■ 당시 법령 부칙의 주요 경과조치 조항 요약:\n" + "\n---\n".join(transitional_snippets[:2])

        return summary_txt
