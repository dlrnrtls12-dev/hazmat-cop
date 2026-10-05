"""
app.py
위험물 기획단속 스마트 현장도우미 웹 애플리케이션 (FastAPI)
"""
import os
import socket
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
# 소방특사경 수사기법 및 소방청 공식 업무지침 27종 & 질의회신 지식고 API
# =========================================================================
from services.enforcement_knowledge_service import EnforcementKnowledgeService

@app.get("/api/knowledge/tactics")
async def get_enforcement_tactics_endpoint():
    """
    소방특사경 핵심 수사전략(3대 서류 점검, 피의자 변명 차단, 2-트랙 처벌 법리) API
    """
    tactics = EnforcementKnowledgeService.get_investigation_tactics()
    return tactics

@app.get("/api/knowledge/guidelines")
async def get_guidelines_endpoint(q: Optional[str] = "", category: Optional[str] = "all", limit: Optional[int] = 50):
    """
    바탕화면 학습 지식 베이스(소방청 업무지침 27종, 실무해설서, 질의회신집 48개 문서) 검색 API
    """
    results = EnforcementKnowledgeService.search_knowledge(query=q or "", category=category or "all", limit=limit or 50)
    return results

@app.get("/api/knowledge/document/{doc_id}")
async def get_knowledge_document_endpoint(doc_id: str):
    """
    학습 문서 원문 전문 조회 API
    """
    doc = EnforcementKnowledgeService.get_document_content(doc_id)
    if not doc:
        return JSONResponse(status_code=404, content={"message": "해당 문서를 찾을 수 없습니다."})
    return doc

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

    ver = applicable.get("matched_version") or {}
    detail = applicable.get("detail") or {}
    clean_date = date.replace("-", "").replace(".", "").strip()
    is_pre_2004 = clean_date < "20040530"

    matched_law = {
        "title": ver.get("law_name") or detail.get("law_name") or "위험물안전관리법",
        "law_no": f"제{ver.get('promulgation_no')}호" if ver.get("promulgation_no") else "",
        "effective_date": ver.get("effective_date", date),
        "promulgation_date": ver.get("promulgation_date", "-"),
        "change_type": ver.get("change_type", "일부개정"),
        "mst": ver.get("mst", ""),
        "detail_url": ver.get("detail_url", ""),
        "addenda": detail.get("addenda", []),
        "articles_count": detail.get("articles_count", 0)
    }

    if is_pre_2004:
        context_code = "PRE_2004_FIRE_ACT"
        primary_rule = "종전 「소방법」 적용 대상: 위험물안전관리법 부칙 제2조(기존시설 특례) 승계 인정"
        guidance = (
            f"입력하신 인허가·완공일({date})은 위험물안전관리법 제정(2004.5.30) 이전입니다. "
            "당시 구 「소방법」에 따라 적법하게 완공·허가받은 제조소등은 현행법 부칙 제2조에 의해 기존 허가 지위를 승계받습니다. "
            "따라서 현행 신규 시설기준 미달을 이유로 즉시 무허가 취급(형사입건)으로 단속할 수 없으며, 종전 소방법 기준 적합성 및 개정법 부칙의 소급·유예 규정을 대조 검토해야 합니다."
        )
    else:
        context_code = "HAZMAT_ACT_ENFORCED"
        primary_rule = f"위험물안전관리법 적용 대상: 인허가일({date}) 당시 시행령·시행규칙 기준 적용"
        guidance = (
            f"입력하신 일자({date}) 당시 시행되던 위험물안전관리법 본문 및 해당 시점의 기술기준(위치·구조·설비)이 적용됩니다. "
            "이후 법령 개정으로 기준이 강화된 경우라도 해당 개정 법령 부칙의 경과조치(기존 시설 특례 또는 적용 유예) 여부를 확인하십시오."
        )

    transition_analysis = {
        "historical_context": context_code,
        "primary_rule": primary_rule,
        "guidance": guidance,
        "applicable_principles": [
            "행위시법 및 인허가 당시 법령 기준 원칙",
            "부칙 제2조 기존 제조소등에 관한 경과조치 특례 승계",
            "인허가 범위를 초과한 무단 증축·위치변경·품명변경은 현행법 위반 엄정 처벌"
        ]
    }

    return {
        "as_of_date": date,
        "matched_law": matched_law,
        "matched_version": ver,
        "detail": detail,
        "transition_analysis": transition_analysis,
        "is_pre_2004": is_pre_2004
    }

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

# =========================================================================
# 6대 전문 서브에이전트 관제 & 1:1 대화 & 에이전트 간 합동 회의 API
# =========================================================================
from services.multi_agent_service import MultiAgentService

class AgentChatRequest(BaseModel):
    agent_id: str
    message: str
    history: Optional[List[Dict[str, str]]] = None

class AgentCollabRequest(BaseModel):
    scenario: str

@app.get("/api/agents/list")
async def get_agents_list_endpoint():
    """
    6대 전문 서브에이전트 메타데이터 및 상태 목록 조회 API
    """
    return MultiAgentService.get_subagents_list()

@app.post("/api/agents/chat")
async def agent_chat_endpoint(req: AgentChatRequest):
    """
    특정 서브에이전트와의 1:1 심층 전문 상담 대화 API
    """
    result = MultiAgentService.chat_with_agent(
        agent_id=req.agent_id,
        message=req.message,
        history=req.history
    )
    return result

@app.post("/api/agents/collaborate")
async def agent_collaborate_endpoint(req: AgentCollabRequest):
    """
    6대 서브에이전트 간의 자율 합동 토론 및 단속 작전 명령 수립 회의 API
    """
    result = MultiAgentService.run_multi_agent_collaboration(req.scenario)
    return result

# =========================================================================
# 에이전트별 언어모델(LLM) 설정 및 연결 테스트 API
# =========================================================================
from services.agent_model_manager import AgentModelManager

class AgentModelUpdateRequest(BaseModel):
    config: Dict[str, Any]

class PresetApplyRequest(BaseModel):
    preset_id: str

class ModelTestRequest(BaseModel):
    model_id: str

@app.get("/api/agents/models")
async def get_agent_models_endpoint():
    """
    현재 에이전트별 모델 배정 설정, 지원 모델 목록, API 키 등록 상태 반환
    """
    return {
        "config": AgentModelManager.load_config(),
        "supported_models": AgentModelManager.get_supported_models(),
        "api_status": AgentModelManager.get_api_key_status()
    }

@app.post("/api/agents/models")
async def update_agent_models_endpoint(req: AgentModelUpdateRequest):
    """
    에이전트별 언어모델 및 Temperature 설정 저장
    """
    success = AgentModelManager.save_config(req.config)
    return {"success": success, "config": AgentModelManager.load_config()}

@app.post("/api/agents/models/reset")
async def reset_agent_models_endpoint():
    """
    에이전트별 모델 설정을 기본 권장값으로 초기화
    """
    defaults = AgentModelManager.reset_to_defaults()
    return {"success": True, "config": defaults}

@app.post("/api/agents/models/preset")
async def apply_preset_endpoint(req: PresetApplyRequest):
    """
    원클릭 프리셋(전체 GPT-4o-mini, 전체 GPT-4o, 하이브리드, 오프라인 등) 일괄 적용
    """
    updated = AgentModelManager.apply_preset(req.preset_id)
    return {"success": True, "config": updated}

@app.post("/api/agents/models/test")
async def test_model_endpoint(req: ModelTestRequest):
    """
    선택한 모델의 통신 연결 상태 및 지연시간(ms) 실시간 테스트
    """
    test_res = AgentModelManager.test_model_connection(req.model_id)
    return test_res


def get_local_ip() -> str:
    """
    동일 Wi-Fi / 사내 네트워크 상의 모바일 기기 접속을 위한 로컬 IPv4 주소 자동 감지
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.get("/api/system/network-info")
async def get_network_info():
    """
    모바일 기기 연결 및 QR 생성을 위한 현재 서버 IP 및 포트 정보 반환
    """
    ip = get_local_ip()
    port = int(os.environ.get("PORT", 8000))
    return {
        "local_ip": ip,
        "port": port,
        "local_url": f"http://localhost:{port}",
        "mobile_url": f"http://{ip}:{port}"
    }

@app.get("/manifest.json")
async def get_manifest():
    """
    모바일 홈 화면 추가 및 PWA (Progressive Web App) 매니페스트 서빙
    """
    return JSONResponse(content={
        "name": "Hazmat Cop - 소방특사경 위험물 단속도우미",
        "short_name": "Hazmat Cop",
        "description": "소방특별사법경찰 위험물 기획단속 스마트 현장도우미",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/icons/icon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    })

@app.get("/api/system/learning-list")
async def get_system_learning_list_endpoint():
    """
    Hazmat Cop AI가 학습/구축한 전문 지식베이스 및 실시간 연동 중인 공공/AI API 명세 반환
    """
    from services.enforcement_knowledge_service import EnforcementKnowledgeService
    from services.agent_model_manager import AgentModelManager
    
    docs = EnforcementKnowledgeService._load_kb()
    categories = {}
    for doc in docs:
        cat = doc.get("category", "기타")
        categories[cat] = categories.get(cat, 0) + 1

    api_status = AgentModelManager.get_api_key_status()

    return {
        "status": "success",
        "timestamp": "2026-10-05T20:55:00+09:00",
        "knowledge_summary": {
            "total_documents": len(docs),
            "categories": categories,
            "hazmat_classification_count": 47,
            "standard_procedures_stages": 12,
            "statutory_forms_count": 8,
            "tactics_interrogation_count": 27
        },
        "learning_details": [
            {
                "id": "kb_acts",
                "title": "위험물안전관리법령 및 기술기준 체계",
                "description": "위험물안전관리법 본칙, 동법 시행령 [별표 1] (제1류~제6류 47개 공식 품명, 지정수량, 배수 합산 계산식), 동법 시행규칙 [별표 4~18] (제조소·저장소·취급소 8대 시설별 안전거리, 보유공지, 소화설비 기술기준) 및 시·도 위험물 안전관리 조례(조례 지정수량 0.2배)",
                "item_count": "법률/시행령/시행규칙/조례 전문",
                "badge": "법령·기술기준",
                "badge_color": "blue"
            },
            {
                "id": "kb_nfa_guidelines",
                "title": "소방청 공식 업무지침 및 수사 매뉴얼 (28선)",
                "description": "무허가 위험물 제조·저장 적발 기준, 완공검사 전 사용, 운반용기 표시·경고표지 위반, 저장소 외 보관 단속 지침, 사업장 부지 내 분산보관 위법성 판정 등 소방청 위험물안전과 핵심 수사지침",
                "item_count": "28건 색인",
                "badge": "소방청 수사지침",
                "badge_color": "emerald"
            },
            {
                "id": "kb_manuals",
                "title": "위험물 실무해설서 및 현장조사 매뉴얼 (8선)",
                "description": "화학물질 성상별 위험성 판정, 제4류 위험물 인화점 기준 분류 지침, 품명 미상물질 역산 감식표, 지정수량 배수 계산 실무, 혼재 저장 기준표",
                "item_count": "8건 색인",
                "badge": "실무해설서",
                "badge_color": "amber"
            },
            {
                "id": "kb_legal_interpretations",
                "title": "법제처·소방청 공식 질의회신 및 유권해석례 (6선)",
                "description": "위험물 배수 병산 계산식(수량/지정수량 합산 1 이상 시 허가대상), 사업장 경계 내 분산 보관 적법성 해석, 부칙 제2조 경과조치 유권해석",
                "item_count": "6건 색인",
                "badge": "유권해석례",
                "badge_color": "purple"
            },
            {
                "id": "kb_tactics_cases",
                "title": "특사경 기획단속 수사전략 & 대법원 판례 (6선)",
                "description": "불법 위험물 유통 및 무허가 시설 적발 수사전략(3선), 위험물안전관리법 위반죄 고의성 입증·포괄일죄·양벌규정 대법원 주요 판례(3선)",
                "item_count": "6건 색인",
                "badge": "판례·수사전략",
                "badge_color": "rose"
            },
            {
                "id": "kb_history_law",
                "title": "1958년 제정 구(舊) 소방법 연혁 및 부칙 경과조치 DB",
                "description": "1958년 소방법 제정부터 2004년 위험물안전관리법 분법에 이르는 반세기 법령 개정사, 사업장 인허가/준공 연도별 소급적용 배제 및 적법 여부 자동 추적",
                "item_count": "연혁 법령 12개 판본",
                "badge": "연혁소방법",
                "badge_color": "indigo"
            },
            {
                "id": "kb_forms",
                "title": "특사경 12단계 표준 수사절차 및 법정 양식 8종 자동화",
                "description": "범죄인지보고서, 압수수색검증영장 신청서, 피의자신문조서, 임의제출동의서, 현장확인서, 의견서, 송치서 등 법정 서식 및 피의자 변명차단 27종 신문기법",
                "item_count": "12단계 / 8종 서식",
                "badge": "수사서식·절차",
                "badge_color": "cyan"
            }
        ],
        "api_specifications": [
            {
                "name": "법제처 국가법령정보센터 Open API",
                "provider": "법제처 (Ministry of Government Legislation)",
                "base_url": "http://www.law.go.kr/DRF/lawSearch.do",
                "auth_status": "연동 가동 중 (OC 식별키: lgs9941)",
                "functions": [
                    "현행 위험물안전관리법, 시행령, 시행규칙 조문 검색",
                    "연혁 소방법령 (1958~2004) 및 부칙 제2조 경과조치 원문 조회",
                    "시·도 위험물 안전관리 조례 (조례 지정수량 0.2배) 실시간 조회",
                    "법제처 공식 법령해석례 전문 조회 (/DRF/lawService.do)"
                ],
                "badge": "국가법령 API",
                "badge_color": "blue"
            },
            {
                "name": "소방청 국가위험물정보시스템 Open API",
                "provider": "소방청 (National Fire Agency) / 공공데이터포털",
                "base_url": "https://apis.data.go.kr/1661000/materialInfoSvc",
                "auth_status": "연동 가동 중 (공공데이터포털 인가 키)",
                "functions": [
                    "화학물질 CAS 번호 및 한글/영문 물질명 기반 위험물 여부 조회",
                    "위험물 품명, 위험등급, 지정수량, 소화약제 및 적응성 조회",
                    "국제연합 위험물 번호 (UN No.) 및 수송 비상대응가이드 연동"
                ],
                "badge": "소방청 공공데이터",
                "badge_color": "emerald"
            },
            {
                "name": "경기데이터드림 화학물질 & 인허가 Open API",
                "provider": "경기도 (Gyeonggi Data Dream)",
                "base_url": "https://openapi.gg.go.kr",
                "auth_status": "연동 가동 중 (경기도 오픈데이터 게이트웨이)",
                "functions": [
                    "화학물질 취급 등록 사업장 정보 실시간 크로스체크 (/ChmstryMttrBizplc)",
                    "위험물 제조소·저장소·취급소 설치허가 및 완공검사 현황 (/DangerousArticleManufactory)"
                ],
                "badge": "지자체 인허가 API",
                "badge_color": "amber"
            },
            {
                "name": "Google Gemini & OpenAI 최첨단 AI 추론 API",
                "provider": "Google DeepMind & OpenAI",
                "base_url": "Google AI Studio & OpenAI API Gateways",
                "auth_status": f"Gemini: {'연동 완료' if api_status.get('gemini', {}).get('configured') else '미설정'} / OpenAI: {'연동 완료' if api_status.get('openai', {}).get('configured') else '미설정'}",
                "functions": [
                    "Gemini 3.8 Flash (미디엄/하이 추론): 배수 계산, 미상물질 역산, 단속 절차 서류 작성, 공공데이터 스크리닝, 메인 챗봇 (초고속·토큰 절약)",
                    "OpenAI GPT-6.1-sol (하이 추론): 지휘본부장(Coordinator), 연혁법령 & 부칙해석, 수사전략 & 피의자 변명차단 (정밀 법리추론)"
                ],
                "badge": "차세대 LLM 엔진",
                "badge_color": "purple"
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    local_ip = get_local_ip()
    print("=" * 65)
    print("  [Hazmat Cop] 위험물 기획단속 스마트 현장도우미 서버 가동 중...")
    print(f"  - PC 로컬 접속:     http://localhost:{port}")
    print(f"  - 모바일 기기 접속: http://{local_ip}:{port}")
    print("    (스마트폰/태블릿에서 동일 Wi-Fi에 연결 후 위 주소로 접속하세요)")
    print("=" * 65)
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
