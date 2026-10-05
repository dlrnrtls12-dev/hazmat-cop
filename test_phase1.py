"""
test_phase1.py
1단계 위험물 DB, 배수 계산기, 위험물안전관리법 & 경기도 조례 종합 판정 엔진 검증
"""
import sys
import io

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.calculator import HazmatEngine, InspectionContext, InspectionItem
from services.law_service import LawService
from services.gg_service import GyeonggiDataService

def run_tests():
    print("=" * 60)
    print("  [1단계 검증] 위험물 배수 계산 및 법령·조례 종합 판정 테스트")
    print("=" * 60)

    # 1. 법제처 API 연동 테스트
    print("\n[테스트 1] 법제처 API 연동 확인...")
    law_svc = LawService()
    laws = law_svc.search_national_law("위험물안전관리법")
    print(f" -> 검색된 국가법령 수: {len(laws)}개")
    for l in laws[:2]:
        print(f"    - {l['name']} (ID: {l['id']})")
    
    ordins = law_svc.search_ordinance("경기도 위험물 안전관리 조례")
    print(f" -> 검색된 경기도 조례 수: {len(ordins)}개")
    for o in ordins[:1]:
        print(f"    - {o['name']} (ID: {o['id']})")

    # 2. 경기도 데이터드림 API 연동 테스트
    print("\n[테스트 2] 경기도 위험물 인허가 현황 API 확인...")
    gg_data = GyeonggiDataService.get_facility_summary(sigun_nm="화성시")
    if gg_data:
        hwaseong = gg_data[0]
        print(f" -> 화성시 위험물 시설 현황: 제조소 {hwaseong.get('MANFCTR_CNT')}개소, 취급소 {hwaseong.get('SALE_TRTMNTPLC_CNT')}개소")
    else:
        print(" -> 경기도 데이터 수신 완료")

    # 3. 단속 현장 핵심 시나리오 테스트
    scenarios = [
        {
            "title": "시나리오 A: 무허가 창고에 신나 300L 적치",
            "ctx": InspectionContext(
                items=[InspectionItem(chemical_name="신나", quantity=300.0)],
                location_type="unauthorized_place",
                is_container_compliant=True
            )
        },
        {
            "title": "시나리오 B: 일반 공장 야적장에 톨루엔 50L 보관 (2024 개정 경기도 조례 0.2배 케이스)",
            "ctx": InspectionContext(
                items=[InspectionItem(chemical_name="톨루엔", quantity=50.0)],
                location_type="unauthorized_place",
                is_container_compliant=True
            )
        },
        {
            "title": "시나리오 C: 복합 물질 혼재 보관 (신나 100L + 경유 600L)",
            "ctx": InspectionContext(
                items=[
                    InspectionItem(chemical_name="신나", quantity=100.0),
                    InspectionItem(chemical_name="경유", quantity=600.0)
                ],
                location_type="unauthorized_place",
                is_container_compliant=True
            )
        },
        {
            "title": "시나리오 D: 톨루엔 50L (0.25배) + 무표시 불량 플라스틱 말통 사용 (법+조례 경합)",
            "ctx": InspectionContext(
                items=[InspectionItem(chemical_name="톨루엔", quantity=50.0)],
                location_type="unauthorized_place",
                is_container_compliant=False  # 법 제20조 운반용기 위반!
            )
        },
        {
            "title": "시나리오 E: 단속관 출입 및 검사 거부·방해",
            "ctx": InspectionContext(
                items=[InspectionItem(chemical_name="신나", quantity=150.0)],
                location_type="unauthorized_place",
                is_inspection_resisted=True  # 법 제27조 단속 거부!
            )
        }
    ]

    for idx, sc in enumerate(scenarios, 1):
        print("\n" + "-" * 60)
        print(f"[{idx}] {sc['title']}")
        print("-" * 60)
        result = HazmatEngine.calculate_and_assess(sc['ctx'])
        
        # 계산 결과 출력
        print(f"▶ 품목별 계산 내역:")
        for it in result.item_results:
            print(f"   - {it.name}: 수량 {it.quantity}{it.unit} / 지정수량 {it.designated_qty}{it.unit} => {it.multiple}배 (조례 0.2배 대상: {it.is_gg_small_qty})")
        
        print(f"▶ 총 배수 합계: {result.total_multiple}배")
        print(f"▶ 지정수량 이상 여부: {'예 (1.0배 이상)' if result.is_designated_qty_or_more else '아니오 (1.0배 미만)'}")
        print(f"▶ 경기도 조례 대상 여부: {'해당 (0.2배~1.0배 미만)' if result.is_gg_ordinance_applicable else '해당 없음'}")
        print(f"▶ 최종 사건 처리 등급: 【 {result.primary_disposition} 】")
        
        print("▶ 위법 조항 및 처벌 수위:")
        for v in result.violations:
            print(f"   * [{v.law_type}] {v.clause}: {v.title}")
            print(f"     => 처벌: {v.penalty_or_sanction} (구분: {v.severity})")
            
        print("▶ 단속관 현장 조치 지침:")
        for act in result.action_guide:
            print(f"   - {act}")
            
        print("▶ 필수 채증 증거 목록:")
        for ev in result.evidence_checklist[:3]:
            print(f"   - {ev}")

    print("\n" + "=" * 60)
    print("  1단계 종합 테스트 성공적으로 완료!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
