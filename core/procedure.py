"""
core/procedure.py
위험물 단속 단계별(전·중·후) 절차 가이드, 관계인 고지문 및 현장 서식 자동 생성기
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from core.calculator import ComprehensiveAssessment

class InspectionTargetInfo(BaseModel):
    business_name: str = Field(description="사업장명 / 상호 (예: (주)한국케미칼)")
    representative_name: str = Field(description="대표자 또는 행위자 성명")
    resident_reg_no: Optional[str] = Field(default="", description="주민등록번호(생년월일)")
    address: str = Field(description="사업장 소재지 (도로명 또는 지번 주소)")
    contact: str = Field(description="연락처")
    inspector_name: str = Field(description="단속 공무원(특사경) 성명")
    inspector_org: str = Field(description="단속 기관 (예: 경기도 소방재난본부 특사경 / 화성소방서)")
    inspection_datetime: Optional[datetime] = Field(default_factory=datetime.now)

class EvidencePhoto(BaseModel):
    photo_id: str
    url: str
    caption: str = "현장 채증 사진"
    timestamp: Optional[str] = ""
    gps_coords: Optional[str] = ""
    category: Optional[str] = "일반"

class StageGuideline(BaseModel):
    stage_name: str
    checklist: List[str]
    notices: List[Dict[str, str]]
    required_documents: List[str]

class ProcedureEngine:
    @staticmethod
    def get_stage_guidelines(stage: str) -> StageGuideline:
        """
        단속 단계별(전/중/후) 체크리스트 및 기본 지침 반환
        """
        if stage == "before":
            return StageGuideline(
                stage_name="[단속 전] 사전 준비 및 계획 단계",
                checklist=[
                    "단속 대상 주소지의 건축물대장 확인 (위험물저장및처리시설 허가 여부 대조)",
                    "소방민원정보시스템(국가위험물정보)을 통한 허가 이력 및 안전관리자 선임 현황 조회",
                    "공무원증 및 소방특별사법경찰관증(신분증표) 필히 지참",
                    "채증 장비 점검 (스마트폰/디지털카메라, 배터리, 메모리, 방폭랜턴)",
                    "시료 채취용기(유리병/갈색병 500mL 2개), 봉인 스티커, 방폭 테이프 준비",
                    "2인 1조 단속 편성 및 안전장구(정전기 방지 안전화, 방독마스크) 착용"
                ],
                notices=[
                    {
                        "title": "사전 점검 원칙",
                        "content": "단속 착수 전 대상지의 주 출입구 및 비상구, 위험물 적치 예상 위치(야적장, 후미진 창고 등)를 로드뷰로 사전 파악합니다."
                    }
                ],
                required_documents=[
                    "단속계획서 (수사계획서)",
                    "현장조사서 양식",
                    "위반사실확인서(적발확인서) 양식",
                    "시료채취확인서 양식"
                ]
            )
        elif stage == "during":
            return StageGuideline(
                stage_name="[단속 중] 현장 착수, 검사 및 채증 단계",
                checklist=[
                    "현장 도착 즉시 관계인(공장장, 대표자, 현장소장 등) 면담 및 신분증표 제시",
                    "위험물안전관리법 제27조 불시점검 법적 근거 명확히 구두 낭독",
                    "관계인 입회 하에 위험물 보관 장소로 이동",
                    "위험물 용기(드럼, 말통, IBC탱크) 라벨, 품명, 용량 실측 및 사진 채증",
                    "납품 거래명세서, 세금계산서, 출하전표, MSDS(물질안전보건자료) 원본 요구 및 촬영",
                    "필요시 시료 채취(관계인 입회하에 2병 분취 후 봉인 스티커 부착 및 관계인 서명)",
                    "위반 배수 1배 이상 등 범죄 혐의 확인 시 즉시 '미란다 원칙(진술거부권)' 고지"
                ],
                notices=[
                    {
                        "title": "1. 현장 신분 제시 및 단속 목적 고지문",
                        "content": "소방특별사법경찰관(또는 소방공무원) ○○○입니다. 「위험물안전관리법」 제27조제1항에 따라 화재예방과 안전 확보를 위해 위험물 저장·취급 실태 검사를 실시합니다."
                    },
                    {
                        "title": "2. 출입·검사 거부/방해 시 경고문",
                        "content": "정당한 사유 없이 소방공무원의 출입·검사를 거부·방해하거나 기피할 경우, 「위험물안전관리법」 제27조제6항 및 제36조에 따라 '1년 이하의 징역 또는 1천만 원 이하의 벌금'에 처해질 수 있습니다."
                    },
                    {
                        "title": "3. 피의자 전환 시 권리 고지 (미란다 원칙 / 형사소송법 제244조의3)",
                        "content": "귀하는 허가받지 아니하고 지정수량 이상의 위험물을 저장·취급한 혐의(또는 법 위반 혐의)로 피의자로 전환되었습니다. 귀하는 일체의 진술을 하지 않거나 개개의 질문에 대해 진술을 거부할 권리가 있습니다. 진술을 거부하더라도 어떠한 불이익도 받지 않으며, 귀하가 행한 진술은 법정에서 유죄의 증거로 사용될 수 있습니다. 또한 변호인을 선임하여 조력을 받을 권리가 있습니다."
                    }
                ],
                required_documents=[
                    "현장조사서 (현장 작성용)",
                    "위반사실확인서 (관계인 자필 서명 날인)",
                    "시료채취확인서 (시료 채취 시)"
                ]
            )
        else: # after
            return StageGuideline(
                stage_name="[단속 후] 서류 정리 및 사법/행정 처리 단계",
                checklist=[
                    "형사사건의 경우: 귀서 즉시 '범죄인지보고서' 작성 및 사건번호 부여(특사경 입건)",
                    "채증 사진 및 동영상 전산 편철 (수사기록 증거목록 작성)",
                    "확보한 시료 국립소방연구원 또는 한국소방산업기술원(KFI) 정밀 성분감정 의뢰",
                    "피의자 출석요구서 발송 및 피의자신문조서 작성 일정 조율",
                    "경기도 조례 위반/과태료 사건의 경우: 시정명령서 발부 및 과태료 부과 사전통지서 통보",
                    "위반 장소의 위험물 안전조치(적법 시설로의 이전, 사용정지 계도) 확인"
                ],
                notices=[
                    {
                        "title": "사법경찰관 송치 시한",
                        "content": "형사입건된 사건은 신속히 피의자 신문 및 조사를 완료하고 관할 검찰청에 기소/불기소 의견으로 송치합니다."
                    }
                ],
                required_documents=[
                    "범죄인지보고서 (형사사건용)",
                    "수사보고서 (단속 경위 및 현장 채증 결과)",
                    "시정명령서 (경기도 조례 위반용)",
                    "과태료 부과 사전통지서 및 의견제출서"
                ]
            )

    @staticmethod
    def generate_violation_confirmation(
        target: InspectionTargetInfo,
        assessment: ComprehensiveAssessment,
        photos: Optional[List[EvidencePhoto]] = None,
        rep_signature: Optional[str] = None,
        insp_signature: Optional[str] = None
    ) -> str:
        """
        단속 현장에서 즉시 출력/서명받을 수 있는 [위반사실확인서(적발확인서)] 자동 생성
        """
        now_str = (target.inspection_datetime or datetime.now()).strftime("%Y년 %m월 %d일 %H시 %M분")
        
        # 적발 품목 요약 텍스트
        item_rows = []
        for it in assessment.item_results:
            c_info = f" | 보관형태: {it.container_desc}" if it.container_desc else ""
            item_rows.append(
                f"- 품명: {it.name}{c_info} (총 {it.quantity}{it.unit}) | 법정지정수량: {it.designated_qty}{it.unit} | 배수: {it.multiple}배"
            )
        items_summary_txt = "\n".join(item_rows) if item_rows else "- 적발 품목 없음"

        # 위반 법조항 요약
        violation_rows = []
        for v in assessment.violations:
            violation_rows.append(f"· [{v.law_type}] {v.clause} ({v.title}) - {v.penalty_or_sanction}")
        violations_txt = "\n".join(violation_rows) if violation_rows else "· 해당 없음"

        # 별첨: 채증 사진 목록
        photos_txt = ""
        if photos and len(photos) > 0:
            photos_lines = ["\n[별첨 1] 단속 현장 채증 사진 목록:"]
            for idx, p in enumerate(photos, 1):
                loc_str = f" | 위치: {p.gps_coords}" if p.gps_coords else ""
                time_str = f" [{p.timestamp}]" if p.timestamp else ""
                photos_lines.append(f"   사진 {idx}. [{p.category}] {p.caption}{time_str}{loc_str}")
            photos_txt = "\n".join(photos_lines)

        # 서명 상태 표기
        rep_sign_str = f"{target.representative_name}  [자필 전자서명 날인 완료 ✓]" if rep_signature else f"{target.representative_name}  (서명 또는 인)"
        insp_sign_str = f"{target.inspector_org} {target.inspector_name}  [특사경 직인/서명 완료 ✓]" if insp_signature else f"{target.inspector_org} {target.inspector_name}  (인)"

        doc = f"""
================================================================================
                           위 반 사 실 확 인 서
================================================================================

1. 대 상 처 인 적 사 항
   - 상  호 (사업장명) : {target.business_name}
   - 소  재  지 : {target.address}
   - 성  명 (대표자/행위자) : {target.representative_name} (주민등록번호: {target.resident_reg_no or '현장 확인'})
   - 연  락  처 : {target.contact}

2. 단 속 일 시 및 장 소
   - 일  시 : {now_str}
   - 장  소 : {target.address} 내 현장

3. 위 반 사 실 (위험물 저장·취급 내역)
{items_summary_txt}

   ▶ 총 지정수량 배수의 합 : {assessment.total_multiple} 배
   ▶ 지정수량 이상 여부    : {'예 (1.0배 이상)' if assessment.is_designated_qty_or_more else '아니오 (1.0배 미만)'}
   ▶ 경기도 조례 대상 여부 : {'해당 (0.2배 이상 ~ 1.0배 미만)' if assessment.is_gg_ordinance_applicable else '해당 없음'}

4. 적 용 법 조 및 위 반 내 역
{violations_txt}
{photos_txt}

5. 진 술 및 확 인
   본인은 상기 일시 및 장소에서 상기 기재와 같이 위험물을 허가 없이 저장·취급하거나
   관련 법령 및 조례를 위반한 사실이 틀림없음을 자인하며, 본 확인서에 서명 날인합니다.

                                        {datetime.now().strftime("%Y년  %m월  %d일")}

                                        확 인 자(관계인) : {rep_sign_str}
                                        조 사 자(단속관) : {insp_sign_str}
================================================================================
"""
        return doc.strip()

    @staticmethod
    def generate_sample_collection_receipt(
        target: InspectionTargetInfo,
        sample_name: str,
        sample_qty: str = "500mL 2병",
        seal_number: str = "SEAL-2026-001",
        photos: Optional[List[EvidencePhoto]] = None,
        rep_signature: Optional[str] = None,
        insp_signature: Optional[str] = None
    ) -> str:
        """
        현장 시료 채취 확인서 (봉인 내역)
        """
        now_str = (target.inspection_datetime or datetime.now()).strftime("%Y년 %m월 %d일 %H시 %M분")
        
        photos_txt = ""
        if photos and len(photos) > 0:
            photos_lines = ["\n[별첨 1] 시료 채취 및 봉인 현장 사진:"]
            for idx, p in enumerate(photos, 1):
                photos_lines.append(f"   사진 {idx}. {p.caption} [{p.timestamp}]")
            photos_txt = "\n".join(photos_lines)

        rep_sign_str = f"{target.representative_name}  [자필 전자서명 날인 완료 ✓]" if rep_signature else f"{target.representative_name}  (서명)"
        insp_sign_str = f"{target.inspector_org} {target.inspector_name}  [특사경 직인/서명 완료 ✓]" if insp_signature else f"{target.inspector_org} {target.inspector_name}  (서명)"

        return f"""
================================================================================
                           시 료 채 취 확 인 서
================================================================================

1. 사 업 장 명 : {target.business_name} (대표자: {target.representative_name})
2. 소   재   지 : {target.address}
3. 채 취 일 시 : {now_str}
4. 채 취 시 료 :
   - 시 료 명 칭 : {sample_name}
   - 채 취 수 량 : {sample_qty} (검사용 1병, 보관용 1병)
   - 봉 인 번 호 : {seal_number}
5. 채 취 사 유 : 위험물 성분 분석 및 인화점·위험물 류별 정밀 감정 의뢰 목적
{photos_txt}

   상기 시료를 관계인 입회 하에 적법하게 채취 및 봉인하였음을 확인합니다.

                                        {datetime.now().strftime("%Y년  %m월  %d일")}

                                        입 회 인(관계인) : {rep_sign_str}
                                        채 취 자(단속관) : {insp_sign_str}
================================================================================
""".strip()

    @staticmethod
    def generate_crime_detection_report(
        target: InspectionTargetInfo,
        assessment: ComprehensiveAssessment,
        photos: Optional[List[EvidencePhoto]] = None,
        insp_signature: Optional[str] = None
    ) -> str:
        """
        특사경 내부 보고용 [범죄인지보고서] 초안
        """
        now_str = (target.inspection_datetime or datetime.now()).strftime("%Y년 %m월 %d일")
        items_desc = ", ".join([f"{it.name} {it.quantity}{it.unit}({it.multiple}배)" for it in assessment.item_results])
        
        photos_txt = ""
        if photos and len(photos) > 0:
            photos_lines = ["\n[증거자료 목록]"]
            for idx, p in enumerate(photos, 1):
                photos_lines.append(f"   증거 {idx}. [{p.category}] {p.caption} (현장 채증 사진)")
            photos_txt = "\n".join(photos_lines)

        insp_sign_str = f"{target.inspector_name}  [특사경 서명/날인 완료 ✓]" if insp_signature else f"{target.inspector_name}  (인)"

        return f"""
================================================================================
                           범 죄 인 지 보 고 서
================================================================================

수신 : 관할 소방서장 (특별사법경찰관)
발신 : 소방특별사법경찰관 {target.inspector_name}

1. 사 건 명 : 위험물안전관리법 위반 (무허가 저장·취급 등)
2. 피 의 자 :
   - 성        명 : {target.representative_name}
   - 상        호 : {target.business_name}
   - 주        소 : {target.address}
   - 연   락   처 : {target.contact}

3. 범 죄 인 지 경 위 :
   2026년 기획단속 계획에 의거, {target.address} 소재 {target.business_name} 사업장에 대한
   불시 위험물 저장·취급 실태 검사를 실시하던 중, 허가를 받지 아니하고 지정수량 이상의
   위험물({items_desc}, 총 {assessment.total_multiple}배)을 보관·취급하고 있는 사실을 현장 적발하여
   범죄 혐의가 상당하므로 형사소송법 제234조 및 특별사법경찰관리 집무규칙에 의거 수사를 개시하고자 함.

4. 적 용 법 조 :
   - 위험물안전관리법 제5조제1항, 제34조의2 (3년 이하의 징역 또는 3천만원 이하의 벌금)
{photos_txt}

5. 조 치 계 획 :
   - 현장 위반사실확인서 징구 및 채증 사진/서류 증거 편철
   - 피의자 출석요구 및 피의자신문조서 작성
   - 관할 검찰청 지휘 건의 및 기소의견 송치 예정

                                        {now_str}

                                        소방특별사법경찰관 : {insp_sign_str}
================================================================================
""".strip()
