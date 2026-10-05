"""
test_phase2.py
2단계 단속 전·중·후 체크리스트, 고지문 및 서류 자동 생성 검증
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.calculator import HazmatEngine, InspectionContext, InspectionItem
from core.procedure import ProcedureEngine, InspectionTargetInfo

def run_tests():
    print("=" * 70)
    print("  [2단계 검증] 단속 절차 체크리스트, 현장 고지문 및 스마트 서류 생성")
    print("=" * 70)

    # 1. 단계별 가이드라인 조회 테스트
    for stage in ["before", "during", "after"]:
        guide = ProcedureEngine.get_stage_guidelines(stage)
        print(f"\n▶ {guide.stage_name}")
        print("  [핵심 체크리스트]")
        for item in guide.checklist[:3]:
            print(f"    √ {item}")
        print("  [현장 고지문 요약]")
        for notice in guide.notices:
            print(f"    📢 {notice['title']}: {notice['content'][:45]}...")
        print(f"  [필수 서류]: {', '.join(guide.required_documents)}")

    # 2. 실제 단속 적발 상황 가정 서류 바인딩 테스트
    print("\n" + "=" * 70)
    print("  [서류 자동 생성 테스트] 신나 300L 무허가 적발 케이스")
    print("=" * 70)

    ctx = InspectionContext(
        items=[InspectionItem(chemical_name="신나", quantity=300.0)],
        location_type="unauthorized_place",
        is_container_compliant=True
    )
    assessment = HazmatEngine.calculate_and_assess(ctx)

    target_info = InspectionTargetInfo(
        business_name="(주)화성정밀도장",
        representative_name="홍길동",
        resident_reg_no="800101-1234567",
        address="경기도 화성시 향남읍 발안공단로 123",
        contact="031-123-4567",
        inspector_name="이국신",
        inspector_org="화성소방서 화재예방과 특사경팀"
    )

    # 위반사실확인서
    conf_doc = ProcedureEngine.generate_violation_confirmation(target_info, assessment)
    print("\n1. 자동 생성된 [위반사실확인서]:")
    print(conf_doc)

    # 시료채취확인서
    sample_doc = ProcedureEngine.generate_sample_collection_receipt(
        target=target_info,
        sample_name="신너(제1석유류 의심 액체)",
        sample_qty="500mL 갈색 유리병 2병",
        seal_number="GG-HS-2026-001"
    )
    print("\n2. 자동 생성된 [시료채취확인서]:")
    print(sample_doc)

    # 범죄인지보고서
    report_doc = ProcedureEngine.generate_crime_detection_report(target_info, assessment)
    print("\n3. 자동 생성된 [범죄인지보고서]:")
    print(report_doc)

    print("\n" + "=" * 70)
    print("  2단계 절차 및 서식 생성 검증 완료!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
