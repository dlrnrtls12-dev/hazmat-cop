"""
services/public_data_service.py
공공데이터포털, 경기도 데이터드림, 법제처 API 통합 서비스
1. 경기도 위험물제조소등 현황 (DangerousArticleManufactory)
2. 경기도 유해화학물질 취급사업장 현황 (ChmstryMttrBizplc)
3. 경기도 업종별 사업체 현황 (Ggindutypebiznes)
4. 법제처 법령해석례 조회 (target=expc)
5. 법제처 행정규칙 조회 (target=admrul)
6. 소방청 국가위험물정보 조회 (materialInfoSvc)
"""
import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class PublicDataService:
    DATA_GO_KR_KEY = os.getenv("DATA_GO_KR_API_KEY", "d76ff92064ea3c34d5001fa67e1fb6939b0c9aa5f631fab5e223f975f6d52b48")
    LAW_API_ID = os.getenv("LAW_API_ID", "lgs9941")

    # 1. 경기도 유해화학물질 취급사업장 현황 조회 (31개 시군 전체 지원)
    @staticmethod
    def search_chemical_businesses(sigun_nm: str = "", biz_name: str = "", max_rows: int = 30) -> List[Dict[str, Any]]:
        url = "https://openapi.gg.go.kr/ChmstryMttrBizplc"
        params = {"Type": "json", "pIndex": 1, "pSize": 100}
        clean_sigun = sigun_nm.strip() if sigun_nm else ""
        if clean_sigun and clean_sigun != "전체":
            params["SIGUN_NM"] = clean_sigun

        results = []
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("ChmstryMttrBizplc", [{}])
                if len(items) > 1:
                    rows = items[1].get("row", [])
                    for r in rows:
                        match_biz = not biz_name or biz_name.lower() in (r.get("ENTRPS_NM") or "").lower()
                        match_chem = not biz_name or biz_name.lower() in (r.get("MANFCTR_CHMSTRY_MTTR_NM") or "").lower()
                        if match_biz or match_chem:
                            results.append({
                                "sigun_nm": r.get("SIGUN_NM", ""),
                                "biz_name": r.get("ENTRPS_NM", ""),
                                "business_type": r.get("INDUTYPE_NM", "유해화학물질취급"),
                                "permit_no": r.get("PERM_NO", ""),
                                "address": r.get("REFINE_ROADNM_ADDR") or r.get("REFINE_LOTNO_ADDR", ""),
                                "main_chemicals": r.get("MANFCTR_CHMSTRY_MTTR_NM", "유해화학물질")
                            })
                        if len(results) >= max_rows:
                            break
        except Exception as e:
            print(f"[PublicDataService] Chemical biz search error: {e}")
        return results

    # 2. 경기도 위험물제조소등 통계 및 현황
    @staticmethod
    def get_hazmat_facilities_summary(sigun_nm: str = "") -> List[Dict[str, Any]]:
        url = "https://openapi.gg.go.kr/DangerousArticleManufactory"
        params = {"Type": "json", "pIndex": 1, "pSize": 50}
        if sigun_nm and sigun_nm != "전체":
            params["SIGUN_NM"] = sigun_nm.strip()
        results = []
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("DangerousArticleManufactory", [{}])[1].get("row", [])
                for r in rows:
                    if not sigun_nm or sigun_nm in r.get("SIGUN_NM", ""):
                        results.append({
                            "sigun_nm": r.get("SIGUN_NM", ""),
                            "manufacture_count": r.get("MANFCTR_CNT", 0),
                            "storage_count": r.get("STORAGEPLC_CNT", 0),
                            "handling_count": r.get("SALE_TRTMNTPLC_CNT", 0),
                            "total_count": (
                                int(r.get("MANFCTR_CNT", 0) or 0) +
                                int(r.get("STORAGEPLC_CNT", 0) or 0) +
                                int(r.get("SALE_TRTMNTPLC_CNT", 0) or 0) +
                                int(r.get("LUBRCTN_TRTMNTPLC_CNT", 0) or 0)
                            )
                        })
        except Exception as e:
            print(f"[PublicDataService] Hazmat facility error: {e}")
        return results

    # 3. 법제처·소방청 법령해석례 실시간 검색 (법제처 expc + 소방청 nfaCgmExpc 통합)
    @staticmethod
    def search_legal_interpretations(query: str = "위험물", max_rows: int = 8) -> List[Dict[str, Any]]:
        results = []
        seen_titles = set()

        # 3-A. 법제처 법령해석례 (expc)
        try:
            url = "http://www.law.go.kr/DRF/lawSearch.do"
            params = {
                "OC": PublicDataService.LAW_API_ID,
                "target": "expc",
                "query": query,
                "type": "XML"
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//expc"):
                    expc_id = (
                        item.findtext("법령해석례일련번호") or
                        item.findtext("해석일련번호") or
                        item.findtext("법령해석일련번호") or ""
                    )
                    link = item.findtext("법령해석례상세링크", "")
                    if not expc_id and "ID=" in link:
                        import re
                        m = re.search(r"ID=(\d+)", link)
                        if m:
                            expc_id = m.group(1)

                    title = (item.findtext("안건명") or "").strip()
                    issue_no = (item.findtext("안건번호") or "").strip()
                    org = (item.findtext("해석기관명") or item.findtext("회신기관") or "법제처").strip()
                    reply_date = (item.findtext("회신일자") or item.findtext("해석일자") or "").strip()

                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        results.append({
                            "id": expc_id,
                            "target": "expc",
                            "title": title,
                            "issue_no": issue_no,
                            "org": org,
                            "reply_date": reply_date
                        })
        except Exception as e:
            print(f"[PublicDataService] MOLEG interpretation search error: {e}")

        # 3-B. 소방청 법령해석례 (nfaCgmExpc)
        try:
            url = "http://www.law.go.kr/DRF/lawSearch.do"
            params = {
                "OC": PublicDataService.LAW_API_ID,
                "target": "nfaCgmExpc",
                "query": query,
                "type": "XML"
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//cgmExpc"):
                    expc_id = (
                        item.findtext("법령해석일련번호") or
                        item.findtext("해석일련번호") or ""
                    )
                    link = item.findtext("법령해석상세링크", "")
                    if not expc_id and "ID=" in link:
                        import re
                        m = re.search(r"ID=(\d+)", link)
                        if m:
                            expc_id = m.group(1)

                    title = (item.findtext("안건명") or "").strip()
                    issue_no = (item.findtext("안건번호") or "").strip()
                    org = (item.findtext("해석기관명") or "소방청").strip()
                    reply_date = (item.findtext("해석일자") or item.findtext("회신일자") or item.findtext("등록일시") or "").strip()

                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        results.append({
                            "id": expc_id,
                            "target": "nfaCgmExpc",
                            "title": title,
                            "issue_no": issue_no,
                            "org": org,
                            "reply_date": reply_date
                        })
        except Exception as e:
            print(f"[PublicDataService] NFA interpretation search error: {e}")

        return results[:max_rows]

    # 3-1. 법제처·소방청 법령해석례 상세 전문 조회 (질의요지, 회답, 이유)
    @staticmethod
    def get_legal_interpretation_detail(expc_id: str, target: str = "") -> Optional[Dict[str, Any]]:
        targets_to_try = [target] if target else ["expc", "nfaCgmExpc"]
        for tgt in targets_to_try:
            try:
                url = "http://www.law.go.kr/DRF/lawService.do"
                params = {
                    "OC": PublicDataService.LAW_API_ID,
                    "target": tgt,
                    "ID": expc_id,
                    "type": "XML"
                }
                resp = requests.get(url, params=params, timeout=6)
                if resp.status_code == 200 and resp.content:
                    root = ET.fromstring(resp.content)
                    title = (root.findtext(".//안건명") or "").strip()
                    issue_no = (root.findtext(".//안건번호") or "").strip()
                    reply_date = (root.findtext(".//해석일자") or root.findtext(".//회신일자") or root.findtext(".//등록일시") or "").strip()
                    dept = (root.findtext(".//해석기관명") or ("소방청" if tgt == "nfaCgmExpc" else "법제처")).strip()
                    ask_dept = (root.findtext(".//질의기관명") or root.findtext(".//질의기관") or "").strip()
                    question = (root.findtext(".//질의요지") or "").strip()
                    reply = (root.findtext(".//회답") or "").strip()
                    reason = (root.findtext(".//이유") or "").strip()

                    if title or question or reply:
                        return {
                            "id": expc_id,
                            "target": tgt,
                            "title": title,
                            "issue_no": issue_no,
                            "reply_date": reply_date,
                            "dept": dept,
                            "ask_dept": ask_dept,
                            "question": question,
                            "reply": reply,
                            "reason": reason
                        }
            except Exception as e:
                print(f"[PublicDataService] Legal detail error (target={tgt}): {e}")
        return None

    # 4. 법제처 위험물 행정규칙(고시/훈령) 검색
    @staticmethod
    def search_admin_rules(query: str = "위험물", max_rows: int = 5) -> List[Dict[str, str]]:
        url = "http://www.law.go.kr/DRF/lawSearch.do"
        params = {
            "OC": PublicDataService.LAW_API_ID,
            "target": "admrul",
            "query": query,
            "type": "XML"
        }
        results = []
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//admrul")[:max_rows]:
                    results.append({
                        "id": item.findtext("행정규칙일련번호", ""),
                        "name": item.findtext("행정규칙명", ""),
                        "org": item.findtext("제정기관명", "소방청"),
                        "issue_date": item.findtext("발령일자", "")
                    })
        except Exception as e:
            print(f"[PublicDataService] Admin rule error: {e}")
        return results
