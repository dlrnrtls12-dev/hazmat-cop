"""
services/case_manager.py
소방특사경 현장단속 건별(Case) 관리 서비스 (저장, 목록 조회, 불러오기, 삭제, 내보내기)
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CASES_FILE = os.path.join(DATA_DIR, "cases.json")

class CaseManager:
    @staticmethod
    def _ensure_data_file():
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(CASES_FILE):
            with open(CASES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    @classmethod
    def get_all_cases(cls) -> List[Dict[str, Any]]:
        cls._ensure_data_file()
        try:
            with open(CASES_FILE, "r", encoding="utf-8") as f:
                cases = json.load(f)
                if not isinstance(cases, list):
                    return []
                # Sort latest first
                cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return cases
        except Exception as e:
            print(f"[CaseManager] Error reading cases: {e}")
            return []

    @classmethod
    def get_case_by_id(cls, case_id: str) -> Optional[Dict[str, Any]]:
        cases = cls.get_all_cases()
        for c in cases:
            if c.get("id") == case_id:
                return c
        return None

    @classmethod
    def save_case(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        cls._ensure_data_file()
        cases = cls.get_all_cases()

        case_id = data.get("id")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not case_id:
            # Generate unique Case ID
            date_prefix = datetime.now().strftime("%Y%m%d-%H%M%S")
            short_uid = uuid.uuid4().hex[:4].upper()
            case_id = f"CASE-{date_prefix}-{short_uid}"
            data["id"] = case_id
            data["created_at"] = now_str
            data["updated_at"] = now_str
            cases.append(data)
        else:
            # Update existing
            found = False
            for i, c in enumerate(cases):
                if c.get("id") == case_id:
                    data["created_at"] = c.get("created_at", now_str)
                    data["updated_at"] = now_str
                    cases[i] = data
                    found = True
                    break
            if not found:
                data["created_at"] = now_str
                data["updated_at"] = now_str
                cases.append(data)

        # Write safely
        temp_file = CASES_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, CASES_FILE)

        return data

    @classmethod
    def delete_case(cls, case_id: str) -> bool:
        cls._ensure_data_file()
        cases = cls.get_all_cases()
        initial_len = len(cases)
        cases = [c for c in cases if c.get("id") != case_id]

        if len(cases) != initial_len:
            temp_file = CASES_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, CASES_FILE)
            return True
        return False

    @classmethod
    def clear_all(cls) -> bool:
        cls._ensure_data_file()
        with open(CASES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return True
