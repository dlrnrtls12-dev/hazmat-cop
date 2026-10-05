"""
core/hazmat_db.py
위험물안전관리법 시행령 [별표 1] 및 경기도 위험물 안전관리 조례 기준 데이터베이스
- 위험물 류별, 품명, 위험등급, 인화점, 주의표지, 저장안전수칙, 소화방법 상세 내장
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class HazmatInfo(BaseModel):
    hazard_class: str = Field(description="위험물 류별 (제1류~제6류)")
    class_name: str = Field(description="류별 명칭 (예: 인화성액체)")
    item_name: str = Field(description="법정 품명 (예: 제1석유류)")
    is_water_soluble: Optional[bool] = Field(default=None, description="수용성 여부")
    unit: str = Field(description="수량 단위 (L 또는 kg)")
    designated_qty: float = Field(description="위험물안전관리법 법정 지정수량")
    gg_small_qty_threshold: float = Field(description="경기도 조례 소량위험물 하한치 (지정수량의 1/5, 즉 0.2배)")
    danger_rank: str = Field(default="II등급", description="위험등급 (I등급, II등급, III등급)")
    flash_point: Optional[str] = Field(default="", description="인화점 또는 발화점 특성")
    caution_sign: str = Field(default="화기주의", description="필수 게시 주의표지 (화기엄금, 물기엄금 등)")
    storage_rules: List[str] = Field(default_factory=list, description="저장·취급 안전수칙")
    extinguish_method: str = Field(default="", description="적응 소화설비 및 소화 방법")
    incompatible_materials: str = Field(default="", description="혼재 및 접촉 금지 물질")
    common_aliases: List[str] = Field(default_factory=list, description="대표 화학물질 및 일상 통칭")

# 위험물안전관리법 시행령 [별표 1] 기준 상세 데이터
HAZMAT_MASTER_DATA: List[HazmatInfo] = [
    # =========================================================================
    # 제1류 산화성고체 (강산화제, 가연물과 접촉 시 급격한 연소·폭발 위험)
    # =========================================================================
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="아염소산염류",
        unit="kg", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="I등급", caution_sign="화기·충격주의 / 가연물 접촉주의",
        storage_rules=[
            "가연물, 유기물, 산류와의 접촉을 엄금할 것",
            "가열, 마찰, 충격을 피하고 통풍이 잘되는 서늘한 냉암소에 보관",
            "용기는 완전 밀폐하여 보관할 것"
        ],
        extinguish_method="다량의 주수에 의한 냉각소화 (소화 시 보호구 착용)",
        incompatible_materials="제2류 가연성고체, 제3류 금수성물질, 제4류 인화성액체, 유기물",
        common_aliases=["아염소산나트륨", "아염소산칼륨"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="염소산염류",
        unit="kg", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="I등급", caution_sign="화기·충격주의 / 가연물 접촉주의",
        storage_rules=[
            "강산(황산 등)과 접촉 시 폭발성 이산화염소 가스가 발생하므로 격리 보관",
            "유기물이나 황, 금속분과의 마찰·충격을 엄금할 것"
        ],
        extinguish_method="다량의 물 주수에 의한 냉각소화 (초기 소화)",
        incompatible_materials="강산, 유기물, 황, 금속분, 제4류 인화성액체",
        common_aliases=["염소산나트륨", "염소산칼륨", "염소산바륨"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="과염소산염류",
        unit="kg", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="I등급", caution_sign="화기·충격주의 / 가연물 접촉주의",
        storage_rules=[
            "열분해 시 산소를 방출하므로 고온체 및 열원과의 접근을 차단할 것",
            "환기가 양호한 건랭소에 보관"
        ],
        extinguish_method="다량의 냉각 주수",
        incompatible_materials="환원제, 유기화합물, 활성 금속",
        common_aliases=["과염소산칼륨", "과염소산나트륨", "과염소산암모늄"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="무기과산화물",
        unit="kg", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="I등급", caution_sign="물기엄금 / 화기주의",
        storage_rules=[
            "물과 격렬히 반응하여 산소를 방출하고 발열하므로 절대 수분 접촉 금지",
            "건조한 곳에 밀봉 보관"
        ],
        extinguish_method="★물 주수 절대 금지! 건조사(마른 모래), 팽창질석, 금속화재용 분말약제 사용",
        incompatible_materials="물, 습기, 산류, 가연물",
        common_aliases=["과산화나트륨", "과산화칼륨", "과산화바륨", "과산화마그네슘"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="질산염류",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="II등급", caution_sign="화기주의 / 가연물 접촉주의",
        storage_rules=[
            "가연물 및 탄소계 유기물과의 접촉 엄금",
            "조해성이 있으므로 습기를 피하여 밀폐 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="가연성 물질, 분말 금속, 강산",
        common_aliases=["질산칼륨", "질산나트륨", "질산암모늄", "초안"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="과망간산염류",
        unit="kg", designated_qty=1000.0, gg_small_qty_threshold=200.0,
        danger_rank="III등급", caution_sign="화기주의 / 가연물 접촉주의",
        storage_rules=["유기물과의 접촉 시 마찰이나 충격만으로 발화 가능하므로 청결 보관"],
        extinguish_method="다량의 물 주수",
        incompatible_materials="유기물, 글리세린, 황산",
        common_aliases=["과망간산칼륨", "과망간산나트륨"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="브롬산염류",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="II등급", caution_sign="화기주의 / 가연물 접촉주의",
        storage_rules=[
            "가연물, 유기물, 산류와의 접촉을 엄금할 것",
            "가열, 충격을 피하고 통풍이 잘되는 서늘한 냉암소 보관"
        ],
        extinguish_method="다량의 냉각 주수",
        incompatible_materials="강산, 가연물, 금속분",
        common_aliases=["브롬산칼륨", "브롬산나트륨", "브롬산바륨"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="요오드산염류",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="II등급", caution_sign="화기주의 / 가연물 접촉주의",
        storage_rules=[
            "환원성 물질 및 유기물과의 접촉 엄금",
            "직사광선 차단 및 밀폐 용기 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="환원제, 유기화합물",
        common_aliases=["요오드산칼륨", "요오드산나트륨"]
    ),
    HazmatInfo(
        hazard_class="제1류", class_name="산화성고체", item_name="중크롬산염류",
        unit="kg", designated_qty=1000.0, gg_small_qty_threshold=200.0,
        danger_rank="III등급", caution_sign="화기주의 / 가연물 접촉주의",
        storage_rules=[
            "강한 산화제로서 가연물과 접촉 시 발화 위험",
            "흡습성이 있으므로 습기를 피하여 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="유기물, 가연성 액체, 알코올류",
        common_aliases=["중크롬산칼륨", "중크롬산나트륨", "중크롬산암모늄", "다이크로뮴산칼륨"]
    ),

    # =========================================================================
    # 제2류 가연성고체 (가연성, 저온 착화성, 연소 시 유독가스)
    # =========================================================================
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="황화린",
        unit="kg", designated_qty=100.0, gg_small_qty_threshold=20.0,
        danger_rank="II등급", caution_sign="화기엄금 / 물기엄금",
        storage_rules=[
            "물과 접촉 시 유독한 황화수소(H2S) 가스가 발생하므로 방수 보관",
            "밀폐용기에 불활성 상태로 보관"
        ],
        extinguish_method="건조사, 이산화탄소 소화기 (주수 소화 엄금)",
        incompatible_materials="물, 습기, 강알칼리, 산화제",
        common_aliases=["삼황화린", "오황화린", "칠황화린"]
    ),
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="적린",
        unit="kg", designated_qty=100.0, gg_small_qty_threshold=20.0,
        danger_rank="II등급", caution_sign="화기엄금",
        storage_rules=[
            "황린과 달리 독성은 적으나 마찰·충격에 민감하므로 충격을 피할 것",
            "산화제와 혼합 시 강한 폭발성 혼합물이 되므로 격리"
        ],
        extinguish_method="다량의 물 주수 또는 건조사",
        incompatible_materials="산화제(제1류, 제6류), 할로겐",
        common_aliases=["붉은인", "적린"]
    ),
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="유황",
        unit="kg", designated_qty=100.0, gg_small_qty_threshold=20.0,
        danger_rank="II등급", caution_sign="화기주의",
        storage_rules=[
            "분진 폭발 위험이 있으므로 분진이 비산하지 않도록 관리",
            "정전기 축적을 방지하고 환기가 양호한 장소에 보관"
        ],
        extinguish_method="물 분무 주수(분진 비산 주의), 포소화설비",
        incompatible_materials="산화제, 강산",
        common_aliases=["황", "유황가루"]
    ),
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="철분",
        unit="kg", designated_qty=500.0, gg_small_qty_threshold=100.0,
        danger_rank="III등급", caution_sign="화기주의 / 물기엄금",
        storage_rules=[
            "물이나 산과 반응하여 수소(H2) 가스를 발생시키므로 습기 차단",
            "건조한 장소에 보관할 것"
        ],
        extinguish_method="★물 주수 절대 금지(수소폭발)! 건조사, 팽창질석, 금속화재용 분말",
        incompatible_materials="물, 산류, 산화제",
        common_aliases=["철가루", "쇳가루"]
    ),
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="금속분",
        unit="kg", designated_qty=500.0, gg_small_qty_threshold=100.0,
        danger_rank="III등급", caution_sign="화기주의 / 물기엄금",
        storage_rules=[
            "미세한 분말 상태로 공기 중에 비산 시 극도로 강력한 분진폭발을 일으킴",
            "수분과의 접촉을 엄격히 방지할 것"
        ],
        extinguish_method="★물 주수 절대 금지! 건조사, 금속화재용 D급 분말약제",
        incompatible_materials="물, 습기, 할로겐, 산화제",
        common_aliases=["알루미늄분", "아연분", "알루미늄가루"]
    ),
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="마그네슘",
        unit="kg", designated_qty=500.0, gg_small_qty_threshold=100.0,
        danger_rank="III등급", caution_sign="화기주의 / 물기엄금",
        storage_rules=[
            "연소 시 2000℃ 이상의 백색 섬광과 고열을 방출",
            "물, 이산화탄소와도 반응하므로 방수 보관"
        ],
        extinguish_method="★물 주수 및 CO2 소화기 절대 금지! 건조사 피복 소화",
        incompatible_materials="물, 산류, 이산화탄소, 할로겐",
        common_aliases=["마그네슘분", "마그네슘리본"]
    ),
    HazmatInfo(
        hazard_class="제2류", class_name="가연성고체", item_name="인화성고체",
        unit="kg", designated_qty=1000.0, gg_small_qty_threshold=200.0,
        danger_rank="III등급", caution_sign="화기엄금",
        storage_rules=["상온에서 인화성 증기를 방출하므로 밀폐 보관하고 화기를 멀리할 것"],
        extinguish_method="포소화약제, 분말, 이산화탄소",
        incompatible_materials="산화제, 점화원",
        common_aliases=["고형알코올", "래커퍼티", "메타알데히드"]
    ),

    # =========================================================================
    # 제3류 자연발화성 및 금수성물질 (공기 중 자연발화, 물과 접촉 시 발열/가연성가스)
    # =========================================================================
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="칼륨",
        unit="kg", designated_qty=10.0, gg_small_qty_threshold=2.0,
        danger_rank="I등급", caution_sign="물기엄금 / 화기엄금",
        storage_rules=[
            "공기 중 수분과 접촉 시 즉시 수소 가스를 내며 폭발 연소",
            "반드시 석유류(유동파라핀, 등유, 경유) 속에 완전히 잠기도록 보관"
        ],
        extinguish_method="★물 주수 금지! 건조사, 팽창질석, 금속화재 전용 소화약제",
        incompatible_materials="물, 습기, 알코올, 산류, 할로겐",
        common_aliases=["포타슘"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="나트륨",
        unit="kg", designated_qty=10.0, gg_small_qty_threshold=2.0,
        danger_rank="I등급", caution_sign="물기엄금 / 화기엄금",
        storage_rules=[
            "물과 반응하여 수산화나트륨과 수소를 생성하며 폭발",
            "파라핀유, 등유, 경유 등 불활성 액체 속에 보관"
        ],
        extinguish_method="★물 주수 금지! 건조사, 팽창진주암",
        incompatible_materials="물, 공기, 산류",
        common_aliases=["소듐"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="황린",
        unit="kg", designated_qty=20.0, gg_small_qty_threshold=4.0,
        danger_rank="I등급", caution_sign="공기접촉엄금 / 화기엄금",
        storage_rules=[
            "자연발화성(착화점 약 34℃)이므로 공기 노출 시 즉시 발화",
            "★물 속에 침지하여 보관(pH 9 이하의 약알칼리수)할 것"
        ],
        extinguish_method="다량의 물 주수(황린을 물로 덮어 냉각 및 차폐)",
        incompatible_materials="공기, 산소, 강산화제, 강알칼리",
        common_aliases=["백린"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="알킬알루미늄",
        unit="kg", designated_qty=10.0, gg_small_qty_threshold=2.0,
        danger_rank="I등급", caution_sign="물기엄금 / 공기접촉엄금",
        storage_rules=[
            "공기 중 자연발화 및 물과 폭발적 반응(메탄/에탄 가스 분출)",
            "불활성 기체(질소, 아르곤)를 충전한 밀폐용기에 보관"
        ],
        extinguish_method="★물 주수 금지! 건조사, 팽창질석",
        incompatible_materials="물, 공기, 할로겐화탄화수소",
        common_aliases=["트리에틸알루미늄", "트리메틸알루미늄"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="알킬리튬",
        unit="kg", designated_qty=10.0, gg_small_qty_threshold=2.0,
        danger_rank="I등급", caution_sign="물기엄금 / 공기접촉엄금",
        storage_rules=[
            "공기 중 자연발화 및 물과 폭발적으로 반응하여 탄화수소 가스 발생",
            "불활성 가스 봉입 밀폐용기에 보관"
        ],
        extinguish_method="★물 주수 절대 금지! 팽창질석, 건조사, 금속화재용 분말약제",
        incompatible_materials="물, 수분, 공기, 산소, 할로겐",
        common_aliases=["메틸리튬", "부틸리튬", "n-부틸리튬"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="알칼리금속및알칼리토금속",
        unit="kg", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="II등급", caution_sign="물기엄금 / 화기주의",
        storage_rules=[
            "물과 접촉 시 수소가스를 발생하며 폭발적 반응",
            "건조한 장소에 밀봉 보관"
        ],
        extinguish_method="★물 주수 절대 금지! 건조사(마른 모래), 금속화재용 분말",
        incompatible_materials="물, 습기, 할로겐, 산화제",
        common_aliases=["리튬", "칼슘", "바륨", "스트론튬"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="유기금속화합물",
        unit="kg", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="II등급", caution_sign="물기엄금 / 공기접촉주의",
        storage_rules=["공기 및 수분과의 접촉을 피하고 불활성 분위기에서 취급"],
        extinguish_method="건조사, 팽창질석",
        incompatible_materials="물, 습기, 공기",
        common_aliases=["디에틸아연", "디에틸마그네슘"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="금속의수소화물",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="III등급", caution_sign="물기엄금 / 화기주의",
        storage_rules=[
            "물과 접촉 시 다량의 가연성 수소가스 발생",
            "건조한 곳에 밀폐 보관"
        ],
        extinguish_method="★물 주수 절대 금지! 건조사, 탄산수소염류 분말",
        incompatible_materials="물, 습기, 강산",
        common_aliases=["수소화나트륨", "수소화칼슘", "수소화리튬", "수소화알루미늄리튬"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="금속의인화물",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="III등급", caution_sign="물기엄금 / 화기주의",
        storage_rules=[
            "물과 반응하여 맹독성의 포스핀(PH3) 가스를 방출하며 자연발화",
            "방수성 밀폐용기 보관 필수"
        ],
        extinguish_method="★물 주수 금지! 건조사, 이산화탄소",
        incompatible_materials="물, 습기, 산류",
        common_aliases=["인화칼슘", "인화알루미늄", "인화아연"]
    ),
    HazmatInfo(
        hazard_class="제3류", class_name="자연발화성및금수성물질", item_name="칼슘또는알루미늄의탄화물",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="III등급", caution_sign="물기엄금 / 화기주의",
        storage_rules=[
            "물과 접촉 시 가연성 가스(아세틸렌 또는 메탄) 발생",
            "건조하고 통풍이 잘되는 곳에 밀봉 보관"
        ],
        extinguish_method="★물 주수 금지! 건조사, 이산화탄소",
        incompatible_materials="물, 습기, 산류",
        common_aliases=["탄화칼슘", "카바이드", "탄화알루미늄"]
    ),

    # =========================================================================
    # 제4류 인화성액체 (현장 적발 빈도 85% 이상 - 증기폭발 및 유류화재)
    # =========================================================================
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="특수인화물",
        is_water_soluble=False, unit="L", designated_qty=50.0, gg_small_qty_threshold=10.0,
        danger_rank="I등급", flash_point="-20℃ 이하 (비점 40℃ 이하)",
        caution_sign="화기엄금",
        storage_rules=[
            "발화점 100℃ 이하 또는 인화점 -20℃ 이하로 극히 위험",
            "통풍이 잘되는 냉암소에 밀봉 보관하고, 정전기 접지 시설 필수",
            "이황화탄소는 물 속에 보관하여 증기 발생 억제"
        ],
        extinguish_method="포소화약제, 이산화탄소, 분말소화기",
        incompatible_materials="강산화제, 점화원, 마찰열",
        common_aliases=["이황화탄소", "디에틸에테르", "에테르", "아세트알데히드", "산화프로필렌"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제1석유류",
        is_water_soluble=False, unit="L", designated_qty=200.0, gg_small_qty_threshold=40.0,
        danger_rank="II등급", flash_point="인화점 21℃ 미만 (상온에서 인화성 증기 지속 방출)",
        caution_sign="화기엄금",
        storage_rules=[
            "상온(21℃ 미만)에서 인화성 유증기가 방출되어 폭발성 혼합기 형성",
            "정전기 축적 방지용 접지 설비 필수",
            "용기는 완전 밀폐하고 지하 또는 실온 40℃ 이하의 환기 양호한 곳에 보관",
            "바닥은 불침투성 재료로 시공하고 배수설비 및 방유턱 구비",
            "제1류, 제6류 산화성물질과 혼재 절대 금지"
        ],
        extinguish_method="일반 포소화설비, 분말(ABC), CO2 소화기 (주수 소화 시 유류 확산 화재 확대)",
        incompatible_materials="제1류 산화성고체, 제6류 산화성액체, 화기, 스파크",
        common_aliases=[
            "휘발유", "가솔린", "신나", "시너", "페인트시너", "에폭시시너", "우레탄시너",
            "톨루엔", "벤젠", "노말헥산", "헥산", "헵탄", "메틸에틸케톤", "MEK",
            "초산에틸", "에틸아세테이트"
        ]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제1석유류",
        is_water_soluble=True, unit="L", designated_qty=400.0, gg_small_qty_threshold=80.0,
        danger_rank="II등급", flash_point="인화점 21℃ 미만 (수용성)",
        caution_sign="화기엄금",
        storage_rules=[
            "물과 잘 섞이는 수용성 인화성 액체이므로 일반 포소화약제 사용 시 거품이 소멸됨",
            "반드시 ★수용성 전용 '내알코올포(수용성포)' 소화약제 구비 필수",
            "밀폐용기 보관 및 환기 장치 상시 가동"
        ],
        extinguish_method="★반드시 내알코올포(Alcohol-resistant foam) 사용, 분말, 이산화탄소",
        incompatible_materials="강산화제, 화기",
        common_aliases=["아세톤", "피리딘", "아크릴로니트릴", "아세토니트릴"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="알코올류",
        is_water_soluble=True, unit="L", designated_qty=400.0, gg_small_qty_threshold=80.0,
        danger_rank="II등급", flash_point="인화점 약 11℃ ~ 13℃ (에탄올/메탄올)",
        caution_sign="화기엄금",
        storage_rules=[
            "1분자 내 탄소수 1~3개인 포화1가 알코올류 (변성알코올 포함)",
            "화재 시 푸른 불꽃으로 연소되어 낮에 불길이 잘 안 보일 수 있으므로 주의",
            "내알코올포 소화약제 비치 필수"
        ],
        extinguish_method="내알코올포, 분말, CO2, 다량의 물 분무 희석",
        incompatible_materials="산화제, 알칼리금속, 강산",
        common_aliases=["메탄올", "메틸알코올", "에탄올", "에틸알코올", "이소프로판올", "IPA", "프로판올", "변성알코올"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제2석유류",
        is_water_soluble=False, unit="L", designated_qty=1000.0, gg_small_qty_threshold=200.0,
        danger_rank="III등급", flash_point="인화점 21℃ 이상 ~ 70℃ 미만",
        caution_sign="화기주의",
        storage_rules=[
            "상온에서는 직접 인화되지 않으나 가열되거나 분무 상태 시 쉽게 인화",
            "여름철 직사광선 차단 및 통풍 유지",
            "누유 방지를 위한 방유제(탱크) 및 드럼통 받침대(드립팬) 설치"
        ],
        extinguish_method="포소화약제, 분말(ABC), 이산화탄소",
        incompatible_materials="강산화제, 고열원",
        common_aliases=[
            "경유", "디젤", "등유", "케로신", "백등유", "보일러등유", "크실렌", "자일렌",
            "테레핀유", "송근유", "솔벤트", "미네랄스피릿", "스티렌모노머", "스티렌"
        ]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제2석유류",
        is_water_soluble=True, unit="L", designated_qty=2000.0, gg_small_qty_threshold=400.0,
        danger_rank="III등급", flash_point="인화점 21℃ 이상 ~ 70℃ 미만 (수용성)",
        caution_sign="화기주의",
        storage_rules=[
            "빙초산 등 산성 물질은 부식성 증기를 유발하므로 내식성 용기 사용",
            "내알코올포 소화기 비치"
        ],
        extinguish_method="내알코올포, 분말, 분무 주수",
        incompatible_materials="강염기, 산화제, 활성 금속",
        common_aliases=["초산", "아세트산", "빙초산", "포름산", "에틸렌글리콜"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제3석유류",
        is_water_soluble=False, unit="L", designated_qty=2000.0, gg_small_qty_threshold=400.0,
        danger_rank="III등급", flash_point="인화점 70℃ 이상 ~ 200℃ 미만",
        caution_sign="화기주의",
        storage_rules=[
            "고인화점이나 점도가 높아 화재 시 진화가 어려움",
            "보일오버(Boil-over) 및 슬롭오버 위험 주의",
            "가열 보관 시설 주변 소화설비 완비"
        ],
        extinguish_method="포소화약제, 분말, 물 분무(유화 소화)",
        incompatible_materials="강산화제",
        common_aliases=["중유", "방청유", "담금질유", "크레오소트유", "클로로벤젠", "중유(B-C유)"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제3석유류",
        is_water_soluble=True, unit="L", designated_qty=4000.0, gg_small_qty_threshold=800.0,
        danger_rank="III등급", flash_point="인화점 70℃ 이상 ~ 200℃ 미만 (수용성)",
        caution_sign="화기주의",
        storage_rules=["수용성 고인화점 액체로서 환기 양호 장소 보관"],
        extinguish_method="내알코올포, 분말, 주수 소화",
        incompatible_materials="산화제",
        common_aliases=["글리세린", "아닐린", "에틸렌디아민", "디에틸렌글리콜"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="제4석유류",
        is_water_soluble=False, unit="L", designated_qty=6000.0, gg_small_qty_threshold=1200.0,
        danger_rank="III등급", flash_point="인화점 200℃ 이상 ~ 250℃ 미만",
        caution_sign="화기주의",
        storage_rules=["고온체 및 가열로 주변에 기름 누출 방지 관리 철저"],
        extinguish_method="포, 분말, 물 분무(강화액)",
        incompatible_materials="산화제",
        common_aliases=["기어유", "윤활유", "실린더유", "엔진오일", "절삭유", "유압유", "절연유"]
    ),
    HazmatInfo(
        hazard_class="제4류", class_name="인화성액체", item_name="동식물유류",
        is_water_soluble=False, unit="L", designated_qty=10000.0, gg_small_qty_threshold=2000.0,
        danger_rank="III등급", flash_point="인화점 250℃ 미만",
        caution_sign="화기주의",
        storage_rules=[
            "건성유(아마인유 등)는 기름걸레 등에 스며들면 상온에서 산화열이 축적되어 ★자연발화 발생",
            "작업 후 기름 묻은 걸레/폐기물은 반드시 뚜껑이 있는 불연성 철제 용기에 담아 폐기할 것"
        ],
        extinguish_method="포소화약제, 분말, 강화액",
        incompatible_materials="산소, 공기(다공성 섬유와 접촉 시)",
        common_aliases=["아마인유", "대두유", "야자유", "피마자유", "동유"]
    ),

    # =========================================================================
    # 제5류 자기반응성물질 (자체 내 산소 함유, 자기 연소 및 폭발성)
    # =========================================================================
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="유기과산화물",
        unit="kg", designated_qty=10.0, gg_small_qty_threshold=2.0,
        danger_rank="I등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=[
            "분자 내 산소를 함유하여 질식소화 불가",
            "마찰, 충격, 직사광선을 피하고 통풍이 잘되는 불연성 냉암소 보관",
            "지정된 분해온도 이하로 냉장 보관"
        ],
        extinguish_method="★질식소화(CO2/모래) 불가! 다량의 주수에 의한 강력한 냉각 소화",
        incompatible_materials="환원제, 유기물, 산류, 직사광선",
        common_aliases=["과산화벤조일", "BPO", "과산화메틸에틸케톤", "MEKPO"]
    ),
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="질산에스테르류",
        unit="kg", designated_qty=10.0, gg_small_qty_threshold=2.0,
        danger_rank="I등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=[
            "극히 예민하여 약간의 충격·마찰로도 폭발",
            "동결 시 파손 주의, 안정제를 첨가하여 보관"
        ],
        extinguish_method="다량의 냉각 주수 (초기 진화 실패 시 대피)",
        incompatible_materials="강산, 알칼리, 금속, 충격",
        common_aliases=["니트로글리세린", "니트로셀룰로오스", "NC", "질화면", "PETN"]
    ),
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="니트로화합물",
        unit="kg", designated_qty=200.0, gg_small_qty_threshold=40.0,
        danger_rank="II등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=["화기 및 고열원으로부터 엄격히 격리하고 충격을 가하지 말 것"],
        extinguish_method="다량의 물 주수",
        incompatible_materials="환원제, 강알칼리",
        common_aliases=["TNT", "트리니트로톨루엔", "피크린산", "TNP"]
    ),
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="니트로소화합물",
        unit="kg", designated_qty=200.0, gg_small_qty_threshold=40.0,
        danger_rank="II등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=[
            "가열 및 충격 시 폭발 위험",
            "통풍이 잘되는 서늘한 냉암소에 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="강산, 강알칼리, 산화제",
        common_aliases=["디니트로소펜타메틸렌테트라민", "DPT"]
    ),
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="아조및디아조화합물",
        unit="kg", designated_qty=200.0, gg_small_qty_threshold=40.0,
        danger_rank="II등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=[
            "열이나 마찰·충격에 민감하며 급격한 분해 폭발 위험",
            "직사광선 차단 및 저온 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="산화제, 강산, 열원",
        common_aliases=["아조비스이소부티로니트릴", "AIBN", "디아조디니트로페놀", "DDNP"]
    ),
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="히드라진유도체",
        unit="kg", designated_qty=200.0, gg_small_qty_threshold=40.0,
        danger_rank="II등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=[
            "공기 중 산화열 축적으로 자연발화 가능",
            "밀폐용기에 불활성 가스 봉입 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="강산화제, 금속산화물",
        common_aliases=["황산히드라진", "염산히드라진"]
    ),
    HazmatInfo(
        hazard_class="제5류", class_name="자기반응성물질", item_name="히드록실아민및그염류",
        unit="kg", designated_qty=100.0, gg_small_qty_threshold=20.0,
        danger_rank="II등급", caution_sign="화기엄금 / 충격주의",
        storage_rules=[
            "가열 시 격렬히 분해 폭발",
            "습기 차단 및 저온 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="산화제, 중금속",
        common_aliases=["히드록실아민", "염산히드록실아민", "황산히드록실아민"]
    ),

    # =========================================================================
    # 제6류 산화성액체 (불연성이지만 강한 부식성과 조연성 산소 방출)
    # =========================================================================
    HazmatInfo(
        hazard_class="제6류", class_name="산화성액체", item_name="과염소산",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="I등급", caution_sign="물기주의 / 가연물 접촉주의",
        storage_rules=[
            "강한 산화력과 부식성을 지니며 유기물과 접촉 시 즉시 발화",
            "내산성 용기에 밀전하여 보관"
        ],
        extinguish_method="다량의 물 주수",
        incompatible_materials="가연물, 유기물, 강환원제",
        common_aliases=["과염소산용액"]
    ),
    HazmatInfo(
        hazard_class="제6류", class_name="산화성액체", item_name="과산화수소",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="I등급", caution_sign="가연물 접촉주의",
        storage_rules=[
            "농도 36wt% 이상인 것만 위험물 해당",
            "가열이나 불순물 혼입 시 폭발적으로 산소를 방출하며 분해",
            "용기 밀전 금지! 통기공(가스 배출구)이 있는 내식성 차광 용기 사용"
        ],
        extinguish_method="다량의 물 주수 (희석 소화)",
        incompatible_materials="가연물, 유기물, 분말 금속",
        common_aliases=["과산화수소수", "과산화수소(36wt%이상)"]
    ),
    HazmatInfo(
        hazard_class="제6류", class_name="산화성액체", item_name="질산",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="I등급", caution_sign="가연물 접촉주의",
        storage_rules=[
            "비중 1.49 이상인 진한 질산만 위험물 해당",
            "유기물과 접촉 시 발열·발화 및 맹독성의 적갈색 이산화질소(NO2) 가스 방출",
            "보호구(내산복, 방독마스크) 필수 착용"
        ],
        extinguish_method="다량의 물 주수 (유독가스 주의)",
        incompatible_materials="유기물, 가연물, 금속분",
        common_aliases=["진한질산", "질산(비중1.49이상)"]
    ),
    HazmatInfo(
        hazard_class="제6류", class_name="산화성액체", item_name="할로겐간화합물",
        unit="kg", designated_qty=300.0, gg_small_qty_threshold=60.0,
        danger_rank="I등급", caution_sign="물기주의 / 가연물 접촉주의",
        storage_rules=[
            "강한 산화성 및 부식성, 물과 접촉 시 폭발적 발열 반응",
            "완전 밀폐된 내식성 특수 용기에 건조 보관"
        ],
        extinguish_method="★물 주수 금지! 건조사, 탄산가스",
        incompatible_materials="물, 수분, 유기화합물",
        common_aliases=["삼불화브롬", "오불화브롬", "오불화요오드"]
    ),
]

def find_hazmat(query: str) -> Optional[HazmatInfo]:
    """
    물질명(품명 또는 일반 별칭)으로 위험물 정보 검색
    """
    if not query:
        return None
    q = query.strip().lower()
    
    # 1. 품명 완전 일치 또는 별칭 일치
    for item in HAZMAT_MASTER_DATA:
        if q == item.item_name.lower():
            return item
        for alias in item.common_aliases:
            if q == alias.lower():
                return item
    
    # 2. 부분 일치 검색
    for item in HAZMAT_MASTER_DATA:
        for alias in item.common_aliases:
            if q in alias.lower() or alias.lower() in q:
                return item
        if q in item.item_name.lower():
            return item
            
    return None

def search_hazmat_catalog(query: str = "") -> List[HazmatInfo]:
    """
    백과사전 검색용 함수 (빈 문자열이면 전체 반환)
    """
    if not query:
        return HAZMAT_MASTER_DATA
    q = query.strip().lower()
    results = []
    for item in HAZMAT_MASTER_DATA:
        matched = False
        if q in item.hazard_class.lower() or q in item.class_name.lower() or q in item.item_name.lower():
            matched = True
        for a in item.common_aliases:
            if q in a.lower():
                matched = True
                break
        if matched:
            results.append(item)
    return results

def search_hazmat_ranked(query: str = "", hazard_class: str = "") -> List[Dict[str, Any]]:
    """
    물질명, 품명, 별칭 기반 검색 점수 랭킹 및 매칭 정보 반환 (자동완성 & 모달 검색용)
    """
    q = query.strip().lower() if query else ""
    target_cls = hazard_class.strip() if hazard_class and hazard_class != "all" else None
    
    scored_results = []
    for item in HAZMAT_MASTER_DATA:
        if target_cls and item.hazard_class != target_cls:
            continue
            
        if not q:
            scored_results.append((10, item, None))
            continue
            
        score = 0
        matched_by = None
        
        # 1. 법정 품명 완전 일치
        if q == item.item_name.lower():
            score = 100
            matched_by = f"품명 일치: {item.item_name}"
        # 2. 대표 별칭 완전 일치
        elif any(q == a.lower() for a in item.common_aliases):
            score = 95
            matching_a = next(a for a in item.common_aliases if q == a.lower())
            matched_by = f"별칭 일치: {matching_a}"
        # 3. 법정 품명 앞부분 시작
        elif item.item_name.lower().startswith(q):
            score = 80
            matched_by = f"품명 시작: {item.item_name}"
        # 4. 별칭 앞부분 시작
        elif any(a.lower().startswith(q) for a in item.common_aliases):
            score = 75
            matching_a = next(a for a in item.common_aliases if a.lower().startswith(q))
            matched_by = f"별칭: {matching_a}"
        # 5. 별칭 부분 일치
        elif any(q in a.lower() for a in item.common_aliases):
            score = 60
            matching_a = next(a for a in item.common_aliases if q in a.lower())
            matched_by = f"별칭 포함: {matching_a}"
        # 6. 품명 부분 일치
        elif q in item.item_name.lower():
            score = 50
            matched_by = f"품명 포함: {item.item_name}"
        # 7. 류별/분류명 일치
        elif q in item.hazard_class.lower() or q in item.class_name.lower():
            score = 40
            matched_by = f"분류: {item.hazard_class} {item.class_name}"
            
        if score > 0:
            scored_results.append((score, item, matched_by))
            
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            **item.model_dump(),
            "matched_by": matched_by,
            "match_score": score
        }
        for score, item, matched_by in scored_results
    ]

def get_hazmat_stats() -> Dict[str, Any]:
    """
    위험물 분류 통계: 전체 등록 품목 수 및 류별 품목 수 반환
    """
    class_meta = {
        "제1류": {"name": "산화성고체", "desc": "강산화성, 가연물 접촉 시 폭발 위험", "color": "blue"},
        "제2류": {"name": "가연성고체", "desc": "저온 착화성, 연소 시 유독가스 발생", "color": "amber"},
        "제3류": {"name": "자연발화성 및 금수성물질", "desc": "공기 노출 시 발화, 물과 접촉 시 수소 등 가연성 가스 발생", "color": "emerald"},
        "제4류": {"name": "인화성액체", "desc": "유류 화재, 증기 폭발, 취급 빈도 최고(85% 이상)", "color": "rose"},
        "제5류": {"name": "자기반응성물질", "desc": "분자 내 산소 함유, 자기 연소 및 폭발, 질식소화 불가", "color": "purple"},
        "제6류": {"name": "산화성액체", "desc": "불연성이지만 강부식성, 가연물 접촉 시 발화 촉진", "color": "cyan"}
    }

    stats = {
        "total_count": len(HAZMAT_MASTER_DATA),
        "classes": {}
    }

    for c, meta in class_meta.items():
        items = [h for h in HAZMAT_MASTER_DATA if h.hazard_class == c]
        stats["classes"][c] = {
            "hazard_class": c,
            "class_name": meta["name"],
            "desc": meta["desc"],
            "color": meta["color"],
            "count": len(items),
            "items": [
                {
                    "item_name": h.item_name,
                    "designated_qty": h.designated_qty,
                    "unit": h.unit,
                    "is_water_soluble": h.is_water_soluble
                }
                for h in items
            ]
        }

    return stats
