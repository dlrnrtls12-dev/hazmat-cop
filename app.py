"""
app.py
위험물 기획단속 스마트 현장도우미 웹 애플리케이션 (FastAPI)
"""
import os
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from core.hazmat_db import find_hazmat, search_hazmat_catalog, search_hazmat_ranked, get_hazmat_stats
from core.calculator import HazmatEngine, InspectionContext, InspectionItem, ComprehensiveAssessment
from core.procedure import ProcedureEngine, InspectionTargetInfo
from services.chatbot import HazmatChatbot
from services.public_data_service import PublicDataService

load_dotenv()

app = FastAPI(title="Hazmat Cop - 위험물 기획단속 현장도우미")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Chatbot
chatbot = HazmatChatbot()

@app.get("/api/hazmat/search")
async def search_hazmat_endpoint(q: Optional[str] = "", cls: Optional[str] = "all"):
    """
    물질정보 통합 검색 API (실시간 자동완성, 모달 검색, 류별 필터 지원)
    """
    results = search_hazmat_ranked(query=q, hazard_class=cls)
    return results

@app.get("/api/hazmat/info")
async def get_hazmat_info(name: str):
    """
    물질명(품명 또는 별칭)으로 상세 위험물 정보 및 안전수칙 조회
    """
    item = find_hazmat(name)
    if not item:
        return JSONResponse(status_code=404, content={"message": f"'{name}' 물질 정보를 찾을 수 없습니다."})
    return item

@app.get("/api/hazmat/catalog")
async def get_hazmat_catalog(q: Optional[str] = ""):
    """
    위험물 백과사전 목록 검색 (검색어 없으면 전체 반환)
    """
    items = search_hazmat_catalog(q)
    return items

@app.get("/api/hazmat/stats")
async def get_hazmat_stats_endpoint():
    """
    위험물 분류 통계 API (전체 품목 수 및 각 류별 품목 수)
    """
    stats = get_hazmat_stats()
    return stats

@app.get("/api/public/chemical-biz")
async def get_chemical_biz(sigun: Optional[str] = "", name: Optional[str] = ""):
    """
    경기도 유해화학물질 취급사업장 조회 API
    """
    results = PublicDataService.search_chemical_businesses(sigun, name)
    return results

@app.get("/api/public/interpretations")
async def get_legal_interpretations(q: Optional[str] = "위험물"):
    """
    법제처·소방청 법령해석례 실시간 목록 조회 API
    """
    results = PublicDataService.search_legal_interpretations(q or "위험물")
    return results

@app.get("/api/public/interpretation-detail/{expc_id}")
async def get_legal_interpretation_detail_endpoint(expc_id: str, target: Optional[str] = None):
    """
    법제처·소방청 법령해석례 상세 전문 (질의요지, 회답, 이유) 조회 API
    """
    detail = PublicDataService.get_legal_interpretation_detail(expc_id, target=target or "")
    if not detail:
        return JSONResponse(status_code=404, content={"message": "법령해석례 상세 정보를 찾을 수 없습니다."})
    return detail

@app.get("/api/public/admin-rules")
async def get_admin_rules(q: Optional[str] = "위험물"):
    """
    위험물 관련 행정규칙(고시/훈령) 조회 API
    """
    results = PublicDataService.search_admin_rules(q or "위험물")
    return results

# =========================================================================
# 법제처 국가법령정보 연혁(eflaw) 및 부칙 경과조치 API
# =========================================================================
from services.law_history_service import LawHistoryService

@app.get("/api/laws/history/search")
async def search_law_history_endpoint(
    q: Optional[str] = "위험물안전관리법",
    as_of: Optional[str] = None,
    target: Optional[str] = "eflaw",
    mode: Optional[str] = "all",
    page: Optional[int] = 1
):
    """
    위험물 국가법령 및 행정규칙 제·개정 연혁 검색 API
    """
    results = LawHistoryService.search_law_history(
        query=q or "위험물안전관리법",
        as_of=as_of,
        target=target or "eflaw",
        mode=mode or "all",
        page=page or 1
    )
    return results

@app.get("/api/laws/history/detail")
async def get_law_history_detail_endpoint(
    mst: str,
    ef_date: Optional[str] = "",
    target: Optional[str] = "eflaw"
):
    """
    과거 연혁 법령 본문 및 부칙 경과조치 전문 조회 API
    """
    detail = LawHistoryService.get_law_history_detail(
        mst=mst,
        effective_date_raw=ef_date or "",
        target=target or "eflaw"
    )
    if not detail:
        return JSONResponse(status_code=404, content={"message": "연혁 법령 상세 정보를 찾을 수 없습니다."})
    return detail

@app.get("/api/laws/history/as-of")
async def get_applicable_law_as_of_endpoint(
    date: str,
    law_name: Optional[str] = "위험물안전관리법"
):
    """
    특정 인허가·완공일자(예: 1999-05-20) 당시 시행 중이던 법령본 및 부칙 자동 매칭 조회 API
    """
    applicable = LawHistoryService.find_applicable_law_as_of(
        law_name=law_name or "위험물안전관리법",
        target_date=date
    )
    if not applicable:
        return JSONResponse(status_code=404, content={"message": f"'{date}' 기준 시행되던 법령 정보를 찾을 수 없습니다."})
    return applicable

# =========================================================================
# 현장 채증 사진 및 전자서명 & 미상 물질 감별 API
# =========================================================================
import base64
import uuid
from datetime import datetime
from core.procedure import EvidencePhoto

class EvidenceUploadRequest(BaseModel):
    image_base64: str
    caption: Optional[str] = "현장 채증 사진"
    timestamp: Optional[str] = None
    gps_coords: Optional[str] = None
    inspector_name: Optional[str] = None
    category: Optional[str] = "일반"

@app.post("/api/evidence/upload")
async def upload_evidence_endpoint(req: EvidenceUploadRequest):
    """
    현장 채증 사진 업로드 및 메타데이터(시간, GPS, 카테고리) 보관 API
    """
    try:
        data = req.image_base64
        if "," in data:
            data = data.split(",", 1)[1]
        img_bytes = base64.b64decode(data)
        photo_id = f"EVD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        filename = f"{photo_id}.jpg"
        filepath = os.path.join("static", "evidence", filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)

        return {
            "photo_id": photo_id,
            "url": f"/static/evidence/{filename}",
            "caption": req.caption or "현장 채증 사진",
            "timestamp": req.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gps_coords": req.gps_coords or "",
            "category": req.category or "일반"
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"사진 저장 실패: {str(e)}"})

# 4단계: 미상 물질 인화점 역산 및 간이 문답 추정 API
@app.get("/api/hazmat/infer-by-flashpoint")
async def infer_by_flashpoint(fp: float, is_water_soluble: bool = False):
    """
    인화점(℃) 기준 제4류 위험물 품명 및 지정수량 역산 API
    """
    if fp < -20:
        item_name = "특수인화물"
        designated_qty = 50.0
        danger_rank = "위험등급 I"
        gg_threshold = 10.0
    elif fp < 21:
        item_name = "제1석유류"
        designated_qty = 400.0 if is_water_soluble else 200.0
        danger_rank = "위험등급 II"
        gg_threshold = 80.0 if is_water_soluble else 40.0
    elif 21 <= fp < 70:
        item_name = "제2석유류"
        designated_qty = 2000.0 if is_water_soluble else 1000.0
        danger_rank = "위험등급 III"
        gg_threshold = 400.0 if is_water_soluble else 200.0
    elif 70 <= fp < 200:
        item_name = "제3석유류"
        designated_qty = 4000.0 if is_water_soluble else 2000.0
        danger_rank = "위험등급 III"
        gg_threshold = 800.0 if is_water_soluble else 400.0
    else:
        item_name = "제4석유류"
        designated_qty = 6000.0
        danger_rank = "위험등급 III"
        gg_threshold = 1200.0

    return {
        "flash_point": fp,
        "is_water_soluble": is_water_soluble,
        "hazard_class": "제4류 (인화성액체)",
        "item_name": item_name,
        "designated_qty": designated_qty,
        "unit": "L",
        "danger_rank": danger_rank,
        "gg_small_qty_threshold": gg_threshold,
        "caution_sign": "화기엄금",
        "inference_basis": f"위험물안전관리법 시행령 [별표 1] 제4류: 인화점 {fp}℃ 측정값 기준 {item_name} 판정"
    }

class SurveyInferRequest(BaseModel):
    is_liquid: bool = True
    odor_type: str = "solvent" # solvent(신나/휘발유), oil(윤활유/기름), chemical(특이취), none(무취)
    water_mixable: bool = False
    usage_type: str = "cleaning" # cleaning(세척), painting(도장), fuel(연료), storage(폐유)

@app.post("/api/hazmat/infer-by-survey")
async def infer_by_survey_endpoint(req: SurveyInferRequest):
    """
    현장 3단계 간이 문답 기반 미상 위험물 임시 추정 및 시료채취 연계 API
    """
    if req.odor_type in ["solvent", "gasoline"] or req.usage_type in ["cleaning", "painting"]:
        item_name = "제1석유류"
        designated_qty = 400.0 if req.water_mixable else 200.0
        danger_rank = "위험등급 II"
        gg_threshold = 80.0 if req.water_mixable else 40.0
        reason = "휘발유·유기용제 취기 및 세척·도장 용도 특성상 인화점 21℃ 미만 제1석유류로 현장 가(假)적용"
    elif req.odor_type == "oil" or req.usage_type in ["fuel", "storage"]:
        item_name = "제2석유류"
        designated_qty = 2000.0 if req.water_mixable else 1000.0
        danger_rank = "위험등급 III"
        gg_threshold = 400.0 if req.water_mixable else 200.0
        reason = "경유·등유·윤활유 특성상 인화점 21℃~70℃ 제2석유류로 현장 가(假)적용"
    else:
        item_name = "제1석유류"
        designated_qty = 200.0
        danger_rank = "위험등급 II"
        gg_threshold = 40.0
        reason = "성분 미상 액체로 안전 및 단속 원칙상 제1석유류 비수용성 가적용 (필수 시료 채취 감정 대상)"

    return {
        "hazard_class": "제4류 (인화성액체)",
        "item_name": item_name,
        "designated_qty": designated_qty,
        "unit": "L",
        "danger_rank": danger_rank,
        "gg_small_qty_threshold": gg_threshold,
        "is_water_soluble": req.water_mixable,
        "inference_basis": reason,
        "sample_required": True
    }

class DocGenerateRequest(BaseModel):
    doc_type: str
    target: InspectionTargetInfo
    assessment: Optional[ComprehensiveAssessment] = None
    photos: Optional[List[EvidencePhoto]] = None
    rep_signature: Optional[str] = None
    insp_signature: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    메인 웹 대시보드 렌더링
    """
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/calculate")
async def calculate_endpoint(ctx: InspectionContext):
    """
    배수 계산 및 종합 위법성 판정 API
    """
    result = HazmatEngine.calculate_and_assess(ctx)
    return result

@app.get("/api/procedure/{stage}")
async def procedure_endpoint(stage: str):
    """
    단속 단계별(before, during, after) 체크리스트 및 고지문 API
    """
    guideline = ProcedureEngine.get_stage_guidelines(stage)
    return guideline

@app.post("/api/documents/generate")
async def generate_document_endpoint(req: DocGenerateRequest):
    """
    단속 현장 스마트 서류(확인서, 시료채취서, 인지보고서) 생성 API (서명 및 채증 사진 연동)
    """
    doc_text = ""
    assessment = req.assessment
    if not assessment:
        dummy_ctx = InspectionContext(
            items=[InspectionItem(chemical_name="신나", quantity=300.0)],
            location_type="unauthorized_place"
        )
        assessment = HazmatEngine.calculate_and_assess(dummy_ctx)

    if req.doc_type == "violation":
        doc_text = ProcedureEngine.generate_violation_confirmation(
            target=req.target,
            assessment=assessment,
            photos=req.photos,
            rep_signature=req.rep_signature,
            insp_signature=req.insp_signature
        )
    elif req.doc_type == "sample":
        doc_text = ProcedureEngine.generate_sample_collection_receipt(
            target=req.target,
            sample_name="시너(제1석유류 의심 액체)",
            sample_qty="500mL 2병",
            seal_number="GG-2026-SEAL-01",
            photos=req.photos,
            rep_signature=req.rep_signature,
            insp_signature=req.insp_signature
        )
    elif req.doc_type == "crime":
        doc_text = ProcedureEngine.generate_crime_detection_report(
            target=req.target,
            assessment=assessment,
            photos=req.photos,
            insp_signature=req.insp_signature
        )
    else:
        doc_text = "지원하지 않는 서식 유형입니다."

    return {"document_text": doc_text}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    위험물 단속 AI 법률 상담 챗봇 API
    """
    answer = chatbot.ask(req.message, req.history)
    return {"response": answer}

if __name__ == "__main__":
    print("=" * 60)
    print("  [Hazmat Cop] 위험물 기획단속 도우미 서버 가동 중...")
    print("  접속 주소: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
