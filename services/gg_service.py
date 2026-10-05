"""
services/gg_service.py
경기도 데이터드림 위험물제조소등 현황 및 유해화학물질 취급사업장 조회 서비스
"""
import requests
from typing import List, Dict, Optional

class GyeonggiDataService:
    HAZMAT_FACILITY_URL = "https://openapi.gg.go.kr/DangerousArticleManufactory"

    @staticmethod
    def get_facility_summary(sigun_nm: Optional[str] = None) -> List[Dict]:
        """
        경기도 시군별 위험물제조소등 현황 통계 조회
        """
        params = {
            "Type": "json",
            "pIndex": 1,
            "pSize": 50
        }
        try:
            resp = requests.get(GyeonggiDataService.HAZMAT_FACILITY_URL, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("DangerousArticleManufactory", [{}])[1].get("row", [])
                if sigun_nm:
                    rows = [r for r in rows if sigun_nm in r.get("SIGUN_NM", "")]
                return rows
        except Exception as e:
            print(f"[GyeonggiDataService] Error: {e}")
        return []
