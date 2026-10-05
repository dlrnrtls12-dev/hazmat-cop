"""
services/nfa_service.py
소방청 국가 위험물 정보 조회 서비스 Open API 연동
"""
import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class NFAService:
    BASE_URL = "https://apis.data.go.kr/1661000/materialInfoSvc/getMaterialList"

    def __init__(self, service_key: Optional[str] = None):
        self.service_key = service_key or os.getenv("DATA_GO_KR_API_KEY")

    def search_chemical(self, chemical_name: str, max_rows: int = 10) -> List[Dict[str, str]]:
        """
        화학물질명으로 소방청 위험물 정보 검색
        """
        params = {
            "serviceKey": self.service_key,
            "pageNo": 1,
            "numOfRows": max_rows,
            "resultType": "json"
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("body", {}).get("items", [])
                results = []
                q = chemical_name.lower().strip()
                for item in items:
                    name = item.get("chemicalname", "")
                    if q in name.lower() or name.lower() in q:
                        results.append({
                            "chemical_name": name,
                            "cas_no": item.get("casno", ""),
                            "un_no": item.get("unno", ""),
                            "hazard_class": item.get("hazardmaterialclass", "")
                        })
                return results
        except Exception as e:
            print(f"[NFAService] Error querying NFA API: {e}")
        return []
