"""
services/law_service.py
법제처 국가법령정보 Open API 연동 서비스
- 위험물안전관리법 및 경기도 위험물 안전관리 조례 실시간 조문 검색
"""
import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class LawService:
    BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"

    def __init__(self, oc: Optional[str] = None):
        self.oc = oc or os.getenv("LAW_API_ID", "lgs9941")

    def search_national_law(self, query: str = "위험물안전관리법") -> List[Dict[str, str]]:
        """
        국가법령 검색 (위험물안전관리법 등)
        """
        params = {
            "OC": self.oc,
            "target": "law",
            "query": query,
            "type": "XML"
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                laws = []
                for law_node in root.findall(".//law"):
                    laws.append({
                        "id": law_node.findtext("법령일련번호", ""),
                        "name": law_node.findtext("법령명한글", ""),
                        "detail_link": law_node.findtext("법령상세링크", "")
                    })
                return laws
        except Exception as e:
            print(f"[LawService] Law search error: {e}")
        return []

    def search_ordinance(self, query: str = "경기도 위험물 안전관리 조례") -> List[Dict[str, str]]:
        """
        자치법규 검색 (경기도 조례 등)
        """
        params = {
            "OC": self.oc,
            "target": "ordin",
            "query": query,
            "type": "XML"
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                ordinances = []
                for node in root.findall(".//law"):
                    ordinances.append({
                        "id": node.findtext("자치법규일련번호", ""),
                        "name": node.findtext("자치법규명", ""),
                        "detail_link": node.findtext("자치법규상세링크", "")
                    })
                return ordinances
        except Exception as e:
            print(f"[LawService] Ordinance search error: {e}")
        return []
