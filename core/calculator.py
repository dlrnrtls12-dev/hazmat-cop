"""
core/calculator.py
위험물 지정수량 배수 계산 및 위험물안전관리법·경기도 조례 종합 위법성 판정 엔진
"""
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from core.hazmat_db import find_hazmat, HazmatInfo

class ContainerSpec(BaseModel):
    capacity: float = Field(description="용기 1개당 용량 (예: 200, 20, 18, 55)")
    unit: str = Field(default="L", description="용기 단위 (L, gal, kg)")
    count: int = Field(default=1, description="용기 개수")

class InspectionItem(BaseModel):
    chemical_name: str = Field(description="물질명 또는 품명 (예: 신나, 톨루엔, 경유)")
    # 다중 중첩 용기 리스트 지원 (예: 200L 4개 + 20L 2개)
    containers: Optional[List[ContainerSpec]] = Field(default=None, description="중첩된 다중 용기 규격 목록")
    # 개별 단일 용기 호환
    container_capacity: Optional[float] = Field(default=None, description="용기 1개당 용량 (예: 200, 18, 55)")
    container_unit: Optional[str] = Field(default="L", description="용기 단위 (L, gal, kg)")
    container_count: Optional[int] = Field(default=1, description="용기 개수")
    # 최종 수량 (직접 지정 또는 용량*개수 자동 계산)
    quantity: Optional[float] = Field(default=None, description="저장 또는 취급 총 수량")
    unit: Optional[str] = Field(default=None, description="수량 단위 (L 또는 kg)")
    container_desc: Optional[str] = Field(default=None, description="상세 용기 내역 설명")

class InspectionContext(BaseModel):
    items: List[InspectionItem]
    location_type: Literal[
        "unauthorized_place",       # 허가받지 아니한 장소 (공장 마당, 일반창고, 공터 등)
        "licensed_facility",        # 기존 허가받은 제조소등
        "temporary_approved",       # 90일 임시저장 승인 장소
        "construction_site"         # 공사현장 등 임시 사용 장소
    ] = Field(default="unauthorized_place", description="단속 장소 구분")
    
    is_container_compliant: bool = Field(
        default=True, 
        description="운반용기 기준(법 제20조: 재질, 표시의무 등) 준수 여부"
    )
    is_inspection_resisted: bool = Field(
        default=False, 
        description="단속 공무원의 출입·검사 거부, 방해, 기피 여부 (법 제27조제6항)"
    )
    safety_manager_status: Literal["normal", "not_appointed", "not_present", "none"] = Field(
        default="none",
        description="안전관리자 선임 및 근무 상태 (허가시설인 경우)"
    )
    technical_violations: List[str] = Field(
        default_factory=list,
        description="현장에서 적발된 기술기준 위반 항목 (예: 방유제 미설치, 혼재 보관, 표지 미부착 등)"
    )

class ItemCalculationResult(BaseModel):
    name: str
    matched_item: Optional[HazmatInfo]
    quantity: float
    unit: str
    container_desc: str = Field(default="", description="용기 규격 및 개수 내역 (예: 200L 드럼 × 3개)")
    designated_qty: float
    multiple: float
    is_gg_small_qty: bool  # 경기도 조례 0.2배 이상 해당 여부
    caution_sign: Optional[str] = "화기주의"

class ViolationDetail(BaseModel):
    law_type: Literal["위험물안전관리법", "경기도 위험물 안전관리 조례"]
    clause: str
    title: str
    penalty_or_sanction: str
    severity: Literal["CRIMINAL", "FINE", "ORDER"] # 형사처벌, 과태료, 시정명령

class SafetyProtocol(BaseModel):
    hazard_level: Literal["CRITICAL", "WARNING", "INFO"] = "INFO"
    explosion_risk: bool = False
    water_reactive: bool = False
    warning_title: str = "현장 안전 기본 수칙 준수"
    warning_desc: str = "위험물 취급 장소 출입 시 환기 및 기본 안전장구를 착용하십시오."
    required_ppe: List[str] = Field(default_factory=list)
    field_cautions: List[str] = Field(default_factory=list)

class ComprehensiveAssessment(BaseModel):
    total_multiple: float = Field(description="전체 위험물 지정수량 배수의 합")
    item_results: List[ItemCalculationResult]
    is_designated_qty_or_more: bool = Field(description="지정수량 1.0배 이상 여부")
    is_gg_ordinance_applicable: bool = Field(description="경기도 조례 소량위험물(0.2배 이상 ~ 1.0배 미만) 해당 여부")
    
    # 종합 위법 사항 리스트
    violations: List[ViolationDetail] = Field(default_factory=list)
    
    # 사건 처리 등급
    primary_disposition: Literal[
        "형사입건 (특사경 수사)",
        "행정 과태료 처분",
        "행정 시정명령",
        "적법 / 특이사항 없음"
    ]
    
    action_guide: List[str] = Field(description="현장 단속관 조치 지침")
    evidence_checklist: List[str] = Field(description="필수 증거 채증 목록")
    safety_protocol: Optional[SafetyProtocol] = None

class HazmatEngine:
    @staticmethod
    def calculate_and_assess(ctx: InspectionContext) -> ComprehensiveAssessment:
        item_results: List[ItemCalculationResult] = []
        total_multiple = 0.0

        for item in ctx.items:
            hazmat = find_hazmat(item.chemical_name)
            if not hazmat:
                # DB에 없는 경우 기본 추정치 또는 검색 실패 기록
                continue

            # 1. 수량 및 용기 환산 처리
            calc_qty = 0.0
            c_desc = ""
            unit = item.unit or hazmat.unit

            # 다중 용기 규격 중첩 처리 (예: 200L 4개 + 20L 2개)
            if item.containers and len(item.containers) > 0:
                total_qty = 0.0
                desc_parts = []
                for c in item.containers:
                    c_count = max(0, c.count)
                    if c_count == 0:
                        continue
                    c_cap = c.capacity
                    cap_str = f"{int(c_cap)}" if float(c_cap).is_integer() else f"{c_cap}"
                    c_u = (c.unit or "L").lower()

                    if c_u in ("gal", "gallon", "갤런"):
                        l_val = round(c_cap * 3.78541 * c_count, 2)
                        total_qty += l_val
                        desc_parts.append(f"{cap_str}gal({round(c_cap*3.78541, 1)}L)×{c_count}개")
                    elif c_u in ("kg", "킬로그램"):
                        kg_val = round(c_cap * c_count, 2)
                        total_qty += kg_val
                        unit = "kg"
                        desc_parts.append(f"{cap_str}kg×{c_count}개")
                    else:
                        l_val = round(c_cap * c_count, 2)
                        total_qty += l_val
                        desc_parts.append(f"{cap_str}L×{c_count}개")

                calc_qty = round(total_qty, 2)
                c_desc = ", ".join(desc_parts) if desc_parts else f"0{unit}"
            elif item.container_capacity is not None and item.container_count:
                count = max(1, item.container_count)
                cap = item.container_capacity
                u = item.container_unit or "L"
                
                if u.lower() in ("gal", "gallon", "갤런"):
                    total_l = round(cap * 3.78541 * count, 2)
                    calc_qty = total_l
                    unit = "L"
                    c_desc = f"{cap}gal(약 {round(cap*3.78541, 1)}L) × {count}개"
                elif u.lower() in ("kg", "킬로그램"):
                    calc_qty = round(cap * count, 2)
                    unit = "kg"
                    c_desc = f"{cap}kg × {count}개"
                else:
                    calc_qty = round(cap * count, 2)
                    unit = "L"
                    c_desc = f"{cap}L × {count}개"
            else:
                unit = item.unit or hazmat.unit
                calc_qty = item.quantity if item.quantity is not None else 0.0
                c_desc = item.container_desc or f"{calc_qty}{unit}"

            # 배수 계산: 저장량 / 법정지정수량
            multiple = round(calc_qty / hazmat.designated_qty, 3)
            total_multiple += multiple
            is_gg_small_qty = (calc_qty >= hazmat.gg_small_qty_threshold)

            item_results.append(ItemCalculationResult(
                name=item.chemical_name,
                matched_item=hazmat,
                quantity=calc_qty,
                unit=unit,
                container_desc=c_desc,
                designated_qty=hazmat.designated_qty,
                multiple=multiple,
                is_gg_small_qty=is_gg_small_qty,
                caution_sign=hazmat.caution_sign if hazmat else "화기주의"
            ))

        total_multiple = round(total_multiple, 3)
        is_designated_or_more = (total_multiple >= 1.0)
        is_gg_ordinance = (0.2 <= total_multiple < 1.0)

        violations: List[ViolationDetail] = []
        action_guides: List[str] = []
        evidence_checks: List[str] = []

        # -------------------------------------------------------------
        # 1. 수량 및 장소에 따른 교차 판단
        # -------------------------------------------------------------
        if is_designated_or_more:
            if ctx.location_type == "unauthorized_place":
                violations.append(ViolationDetail(
                    law_type="위험물안전관리법",
                    clause="제5조제1항, 제34조의2",
                    title="무허가 위험물 저장·취급 (지정수량 1배 이상)",
                    penalty_or_sanction="3년 이하의 징역 또는 3천만원 이하의 벌금",
                    severity="CRIMINAL"
                ))
                action_guides.append("🚨 [형사사건] 무허가 위험물 취급 적발! 즉시 관계인 피의자 전환 및 진술거부권 고지")
                evidence_checks.extend([
                    "위반 장소 전경 및 저장·취급 상태 사진/동영상 채증",
                    "위험물 드럼/탱크 라벨 및 용량 표기 실측 사진",
                    "납품 거래명세서, 세금계산서, 출하증명서 원본 또는 사본 확보",
                    "현장 시료 채취(2인 입회 봉인 및 시료채취확인서 작성)"
                ])
            elif ctx.location_type == "licensed_facility":
                # 허가시설이지만 배수 초과 또는 품명 변경인 경우
                violations.append(ViolationDetail(
                    law_type="위험물안전관리법",
                    clause="제6조제1항, 제35조",
                    title="제조소등의 변경허가 미필 (수량 또는 품명 무단 변경)",
                    penalty_or_sanction="1년 이하의 징역 또는 1천만원 이하의 벌금",
                    severity="CRIMINAL"
                ))
                action_guides.append("허가증 상의 허가 품명 및 지정수량 배수 초과 여부 정밀 대조")

        elif is_gg_ordinance:
            # 0.2배 이상 ~ 1.0배 미만: 경기도 조례 소량위험물 기준 적용
            violations.append(ViolationDetail(
                law_type="경기도 위험물 안전관리 조례",
                clause="제5조, 제6조",
                title="소량위험물(0.2배~1.0배 미만) 저장·취급 기술기준 위반 검토",
                penalty_or_sanction="시정명령 및 불이행 시 200만원 이하 과태료 (위험물법 제39조 연계)",
                severity="ORDER"
            ))
            action_guides.append("⚠️ [경기도 조례 적용] 지정수량 1/5(0.2배) 이상 관리대상. 소량위험물 보관 장소의 방화구획, 접지, 환기설비 등 기준 점검")
            evidence_checks.extend([
                "소량위험물 적치 장소 사진 및 실측 수량표",
                "방화상 안전한 장소 여부 및 위험물 표지 부착 상태 확인"
            ])

        # -------------------------------------------------------------
        # 2. 운반용기 기준 위반 검토 (위험물안전관리법 제20조)
        # -> ★ 중요: 지정수량 미만이라도 법 제20조는 전국 공통 적용!
        # -------------------------------------------------------------
        if not ctx.is_container_compliant:
            violations.append(ViolationDetail(
                law_type="위험물안전관리법",
                clause="제20조, 제39조",
                title="위험물 운반용기의 수납·표시 기준 위반",
                penalty_or_sanction="200만원 이하의 과태료",
                severity="FINE"
            ))
            action_guides.append("📌 [위험물법 과태료] 용기 미표시(품명·수량·화기엄금 미기재) 또는 부적합 용기 사용 과태료 부과 절차 진행")
            evidence_checks.append("부적합 운반용기(표시 누락, 변형된 말통 등) 사진 채증")

        # -------------------------------------------------------------
        # 3. 단속 거부·방해 검토 (위험물안전관리법 제27조제6항)
        # -------------------------------------------------------------
        if ctx.is_inspection_resisted:
            violations.append(ViolationDetail(
                law_type="위험물안전관리법",
                clause="제27조제6항, 제36조",
                title="소방공무원의 출입·검사 거부·방해 또는 기피",
                penalty_or_sanction="1년 이하의 징역 또는 1천만원 이하의 벌금",
                severity="CRIMINAL"
            ))
            action_guides.append("🚨 [출입거부 즉시 경고] 법 제27조에 따른 벌칙(1년 징역/1천만원 벌금)을 낭독하고 불응 시 경찰 입회 요청")
            evidence_checks.append("출입 거부 정황 녹음 또는 동영상 채증(거부자 인적사항 및 거부 발언 확보)")

        # -------------------------------------------------------------
        # 4. 안전관리자 위반 (허가시설인 경우)
        # -------------------------------------------------------------
        if ctx.location_type == "licensed_facility":
            if ctx.safety_manager_status == "not_appointed":
                violations.append(ViolationDetail(
                    law_type="위험물안전관리법",
                    clause="제15조제2항, 제37조",
                    title="위험물안전관리자 미선임",
                    penalty_or_sanction="500만원 이하의 벌금",
                    severity="CRIMINAL"
                ))
            elif ctx.safety_manager_status == "not_present":
                violations.append(ViolationDetail(
                    law_type="위험물안전관리법",
                    clause="제15조제3항, 제39조",
                    title="안전관리자 부재 시 대리자 미지정 또는 직무태만",
                    penalty_or_sanction="200만원 이하의 과태료",
                    severity="FINE"
                ))

        # -------------------------------------------------------------
        # 5. 최종 사건 등급(Primary Disposition) 결정
        # -------------------------------------------------------------
        has_criminal = any(v.severity == "CRIMINAL" for v in violations)
        has_fine = any(v.severity == "FINE" for v in violations)
        has_order = any(v.severity == "ORDER" for v in violations)

        if has_criminal:
            primary_disposition = "형사입건 (특사경 수사)"
        elif has_fine:
            primary_disposition = "행정 과태료 처분"
        elif has_order:
            primary_disposition = "행정 시정명령"
        else:
            primary_disposition = "적법 / 특이사항 없음"
            action_guides.append("현장 법적 기준 및 조례 기준 충족 확인. 일상 화재예방 안전지도 권고.")

        # -------------------------------------------------------------
        # 6. 단속관 안전 및 방폭 주의 프로토콜 (Safety Protocol)
        # -------------------------------------------------------------
        has_c4_petro1 = any(
            ("제1석유류" in it.name or "특수인화물" in it.name or "신나" in it.name or "시너" in it.name or "톨루엔" in it.name or "휘발유" in it.name)
            for it in item_results
        )
        has_water_banned = any("물기엄금" in (it.caution_sign or "") for it in item_results)

        req_ppe = ["정전기 방지 안전화", "내유/내화학 안전장갑"]
        cautions = []
        explosion_risk = False
        water_reactive = False

        if has_c4_petro1 or total_multiple >= 1.0:
            hazard_level = "CRITICAL"
            explosion_risk = True
            warning_title = "🚨 가연성 유증기 폭발 하한계 체류 위험 (방폭 경보)"
            warning_desc = "인화점 21℃ 미만 유기용제(신나, 톨루엔 등) 증기가 밀폐 공간에 체류할 수 있습니다. 현장 환기 전 일반 스마트폰 플래시 및 비방폭 스위치 조작을 엄금합니다."
            req_ppe.extend(["유기화합물용 갈색 정화통 방독마스크", "방폭 손전등/헤드랜턴"])
            cautions.append("현장 진입 전 창문 및 출입문을 개방하여 자연 환기 실시")
            cautions.append("단속관 스마트폰 조작 시 정전기 방지 및 스파크 주의")
            cautions.append("현장 내 흡연 및 라이터, 휴대전화 충전기 등 점화원 일체 차단")
        elif has_water_banned:
            hazard_level = "CRITICAL"
            water_reactive = True
            warning_title = "🚨 금수성 물질 물 주수 절대 금지 (수소 폭발 경보)"
            warning_desc = "물과 접촉 시 급격한 발열 및 폭발성 수소/아세틸렌 가스를 발생시키는 물질입니다."
            req_ppe.extend(["전면형 화학보호마스크", "내약품성 화학보호복"])
            cautions.append("옥내외 소화전 및 수계 소화설비 방수 절대 엄금")
            cautions.append("마른 모래(건조사), 팽창질석, 금속화재용(D급) 소화약제 확보 확인")
        elif total_multiple >= 0.2:
            hazard_level = "WARNING"
            warning_title = "⚠️ 위험물 취급 현장 유독가스 및 화재 안전 주의"
            warning_desc = "지정수량 0.2배 이상 소량위험물 저장 장소입니다. 방독면과 보호장구를 착용하십시오."
            req_ppe.append("방진·방독 겸용 마스크")
            cautions.append("용기 전도 및 파손 여부 점검 시 조심스럽게 접근")
        else:
            hazard_level = "INFO"
            warning_title = "ℹ️ 현장 표준 안전 장구 착용 권고"
            warning_desc = "일반 단속 안전 지침을 준수하여 현장 확인을 진행하십시오."
            req_ppe.append("기본 방진마스크")

        safety_protocol = SafetyProtocol(
            hazard_level=hazard_level,
            explosion_risk=explosion_risk,
            water_reactive=water_reactive,
            warning_title=warning_title,
            warning_desc=warning_desc,
            required_ppe=list(dict.fromkeys(req_ppe)),
            field_cautions=cautions
        )

        return ComprehensiveAssessment(
            total_multiple=total_multiple,
            item_results=item_results,
            is_designated_qty_or_more=is_designated_or_more,
            is_gg_ordinance_applicable=is_gg_ordinance,
            violations=violations,
            primary_disposition=primary_disposition,
            action_guide=action_guides,
            evidence_checklist=evidence_checks,
            safety_protocol=safety_protocol
        )
