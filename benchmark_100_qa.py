"""
benchmark_100_qa.py
100회 위험물 민원 질의응답 사례집 스타일 자체 검증 및 정밀 분석 벤치마크 스크립트
"""
import os
import sys
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

from services.chatbot import HazmatChatbot

# 100개 실무 질의 풀 생성 (8대 전 분야)
QUESTIONS = [
    # 1. 지정수량 배수 산정 및 품명 판정 (20문항)
    "제1석유류 비수용성 100L와 제2석유류 비수용성 500L를 같은 창고에 보관 중입니다. 지정수량 배수 합산과 허가 대상 여부는?",
    "인화점 18도인 유기용제가 물 100g에 5g만 녹고 층분리가 발생합니다. 수용성으로 인정받아 400L 기준을 적용할 수 있습니까?",
    "기계작동유(제4석유류)를 공정 가열탱크에서 220도로 가열하여 사용할 때 품명이 제3석유류로 변경됩니까?",
    "상온에서 끈적한 점성을 가진 우레탄 도료가 인화점 15도입니다. 액체가 아니라는 이유로 위험물에서 제외될 수 있습니까?",
    "에탄올 70% 함유 손소독제 2,000L를 물류창고에 보관할 때 위험물안전관리법상 알코올류에 해당하여 허가를 받아야 합니까?",
    "식당용 젤 형태의 고형알코올 2,000kg을 창고에 보관할 때 제4류 알코올류인가요, 제2류 인화성고체인가요?",
    "폐기물관리법에 따라 사업장폐기물로 보관 중인 폐신나(인화점 10도) 2,000L에 위험물안전관리법이 중복 적용됩니까?",
    "아세트알데히드는 인화점이 -38도이고 비점이 21도입니다. 제1석유류인가요, 특수인화물인가요?",
    "동식물유류 5,000L(요오드가 140인 건성유)를 공장에 보관할 때 지정수량 배수는 몇 배입니까?",
    "제3석유류 에틸렌글리콜 4,000L는 수용성 위험물인데 지정수량 몇 배에 해당합니까?",
    "인화점이 75도인 절삭유 3,000L는 제3석유류 비수용성입니까 수용성입니까?",
    "휘발유 100L와 경유 800L를 함께 보관할 때 총 지정수량 배수 합계는 얼마입니까?",
    "제2류 황화린 50kg과 적린 50kg을 동일 장소에 보관 시 지정수량 배수의 합계는?",
    "제1류 아염소산염류 30kg과 질산염류 150kg을 보관할 때 허가 대상에 해당합니까?",
    "제3류 황린 10kg과 나트륨 25kg을 함께 저장할 때 총 배수는 몇 배입니까?",
    "중유(제3석유류 비수용성) 1,500L는 지정수량 1배 이상입니까 미만입니까?",
    "제5류 유기과산화물 20kg은 지정수량 몇 배에 해당합니까?",
    "제6류 과산화수소 농도 40중량%인 물질 600kg은 위험물에 해당합니까?",
    "농도 55%인 에탄올 수용액 1,000L는 제4류 알코올류에 해당합니까?",
    "윤활유(제4석유류) 5,000L를 드럼에 넣어 보관할 때 허가 대상입니까?",

    # 2. 무허가 저장 및 취급 (15문항)
    "공장 보수공사를 위해 20일간 제1석유류 2,000L를 옥외에 임시보관하려 합니다. 임시저장 승인 최대 기간은?",
    "16,000L 기름을 실은 탱크로리가 밤늦게 도착하여 공장 마당에 밤새 주차해 두었습니다. 무허가 저장에 해당합니까?",
    "자동 도장기계 옆에 당일 사용할 신나 말통 5개(100L)를 호스로 연결해 둔 행위는 저장인가요 취급인가요?",
    "경기도 화성시 공장에서 신나 80L(지정수량 0.4배)를 야외에 방치 시 시·도 조례 위반으로 과태료 처분을 받습니까?",
    "아파트 지하 비상발전기실에 1,500L 경유 일체형 연료탱크를 설치할 때 소방서 허가를 받아야 합니까?",
    "1,000L 플라스틱 IBC탱크 2개에 절삭유(2,000L)를 채워 공장 뒤편 맨땅에 보관하는 것이 적법합니까?",
    "사용중지(휴지) 신고된 옥내저장소에 급한 물량이 들어와 3일간 제1석유류 500L를 임시 적치했습니다. 위법입니까?",
    "연구실에서 실험용으로 에테르 60L를 시약장에 보관 중입니다. 지정수량 50L 초과인데 무허가 저장입니까?",
    "건설현장에서 포크레인 주유용으로 200L 드럼 2개(경유 400L)를 야외에 두고 주유 중입니다. 법적 위반인가요?",
    "위험물 제조소 허가를 받지 않은 일반 공장에서 톨루엔 500L를 교반기에 넣고 배합 생산하면 어떤 처벌을 받습니까?",
    "운반용기 기준에 적합하지 않은 일반 생수통에 휘발유 20L를 담아 보관하면 어떤 벌칙을 받습니까?",
    "임시저장 승인을 신청하지 않고 공장 마당에 톨루엔 드럼을 2일간 보관하다 적발되면 벌칙은?",
    "식품공장에서 에탄올 95% 주정 1,000L를 세척용으로 일반 창고에 보관하면 위험물법 위반입니까?",
    "농가에서 난방용 등유 1,500L를 홈로리용 플라스틱 탱크에 보관할 때 허가 기준은?",
    "위험물 저장소 허가 부지 경계선 바깥 공터에 빈 드럼통 50개를 쌓아두어도 됩니까?",

    # 3. 안전거리 및 보유공지 (15문항)
    "제조소 외벽에서 인근 주택까지 안전거리 측정 시 기산점은 건물 벽체인가요, 돌출된 처마·배관 끝단인가요?",
    "제조소 부지 내에 위치한 직원 기숙사도 10m 안전거리 보호대상 주거시설에 해당합니까?",
    "인근 주택과의 안전거리 10m가 부족하여 높이 3m 방화벽을 설치하면 안전거리를 단축할 수 있습니까?",
    "옥외저장탱크 주위 3m 보유공지에 빈 플라스틱 파레트와 일반 자재를 쌓아두면 법 위반입니까?",
    "제조소 외벽 바깥으로 대기오염방지설비인 RTO를 증설할 때 보유공지 5m의 기산점은 어디입니까?",
    "제조소 보유공지 3m 중 1.5m 구간이 45도 경사의 옹벽 법면인 경우 보유공지로 인정됩니까?",
    "위험물시설 부지의 보유공지 일부가 도시계획 도로로 편입되어 포장된 경우 계속 사용이 가능합니까?",
    "하나의 방유제 내에 옥외저장탱크 3기를 나란히 배치할 때 탱크 상호 간 이격거리 기준은?",
    "옥내저장소 외벽에 방화상 유효한 담을 설치하면 보유공지를 전면 면제받을 수 있습니까?",
    "제조소와 35kV 특고압 가공전선 사이의 안전거리는 몇 미터 이상 이격해야 합니까?",
    "학교 및 유치원과 위험물 제조소 사이의 법정 안전거리는 몇 미터 이상입니까?",
    "지정문화재와 위험물 옥외탱크저장소 사이의 안전거리 기준은 몇 미터입니까?",
    "지하탱크저장소에도 지상에 보유공지를 반드시 확보해야 합니까?",
    "간이탱크저장소 주위에 확보해야 하는 보유공지 너비는 몇 미터입니까?",
    "옥외저장소의 보유공지 너비는 저장하는 위험물의 지정수량 배수에 따라 어떻게 달라집니까?",

    # 4. 방유제 및 구조설비 (15문항)
    "동일 방유제 안에 1만L, 2만L, 3만L 옥외탱크 3기가 있을 때 방유제 최소 용량은 몇 L입니까?",
    "방유제를 콘크리트 대신 토사(흙담)로만 쌓아도 적법합니까?",
    "위험물 이송 배관이 방유제 벽체를 직접 관통하여 지나가도 됩니까?",
    "옥내 위험물 취급소 바닥에 에폭시만 칠하고 집유설비나 배수구를 설치하지 않아도 됩니까?",
    "인화성 증기가 체류하는 장소의 배출설비 모터는 일반 모터를 사용해도 됩니까?",
    "톨루엔 이송 배관의 정전기 방지 접지설비 접지저항 기준값은 몇 옴 이하입니까?",
    "위험물 이송 배관 신설 시 실시해야 하는 수압시험 압력 기준은 설계압력의 몇 배입니까?",
    "제1석유류 옥외저장탱크에 질소가스를 봉입하는 설비를 의무적으로 설치해야 하는 기준은?",
    "방유제 높이 기준은 최소 몇 미터 이상 몇 미터 이하로 축조해야 합니까?",
    "용량 1,000만L 이상의 대형 옥외저장탱크 방유제에 설치해야 하는 간이칸막이 높이와 용량은?",
    "방유제 내에 고인 빗물을 외부로 배출하기 위해 설치하는 배수구 개폐밸브의 정상 상태는?",
    "옥외탱크 방유제 내부에 위험물 이송용 펌프설비를 설치할 수 있습니까?",
    "인화점 21도 미만 위험물 옥외탱크에 설치하는 통기관은 무변통기관인가요 대기밸브부착 통기관인가요?",
    "지하저장탱크를 콘크리트 탱크실 없이 직접 흙에 묻을 수 있는 이중벽탱크의 조건은?",
    "옥내저장탱크의 통기관 끝단에 설치해야 하는 인화방지망의 구리망 규격은 몇 메시 이상입니까?",

    # 5. 저장소 및 취급소별 기술기준 (15문항)
    "옥내저장소는 단층 건물이어야 합니까, 3층 건물 중 2층에 설치할 수 있습니까?",
    "이동탱크저장소(탱크로리) 차량을 아파트 지하주차장에 야간 주차해도 됩니까?",
    "허가받은 옥외저장소에 인화점 10도인 신나 드럼을 야적 보관할 수 있습니까?",
    "간이탱크저장소 1개소당 설치 가능한 최대 탱크 기수와 1기당 용량 한도는?",
    "지하 암반탱크저장소는 원유 누설을 방지하기 위해 어떤 시스템을 유지합니까?",
    "주유취급소 부지 내에 2층 카페나 전기차 급속충전기를 증설하는 것이 허용됩니까?",
    "스프레이 분무도장 부스 일반취급소의 바닥면적 1제곱미터당 최소 배출풍량 기준은?",
    "탱크로리에서 200L 드럼으로 제1석유류를 옮겨 담는 소분 작업은 어떤 취급소 허가를 받아야 합니까?",
    "제1종 판매취급소와 제2종 판매취급소가 저장·취급할 수 있는 최대 배수는 각각 몇 배입니까?",
    "석유화학단지 도로 지하에 매설하는 위험물 배관의 지하 매설 깊이(토피) 기준은 몇 미터입니까?",
    "주유취급소의 고정주유설비 노즐에서 주유공지 도로 경계선까지의 이격거리 기준은?",
    "주유소 캐노피 배선 및 조명기구는 어떤 방폭구조를 갖추어야 합니까?",
    "옥내주유취급소의 건축물 윗층에 공동주택이나 일반 사무실이 있어도 됩니까?",
    "선박에 기름을 직접 주유하는 해상주유취급소의 배관 기술기준은?",
    "화물차 전용 자가주유취급소에 일반 승용차를 주유해도 법 위반입니까?",

    # 6. 소화설비, 안전관리자 및 행정절차 (10문항)
    "직경 25m, 높이 15m인 톨루엔 옥외탱크는 소화난이도등급 몇 등급에 해당합니까?",
    "옥외탱크 고정포방출구용 3% 수성막포 소화약제 필요 수량 산정 공식은?",
    "위험물 제조소에 설치되는 소방배관도 「소방시설의 내진설계 기준」 흔들림방지 버팀대를 설치해야 합니까?",
    "대형 옥외원유탱크에 설치해야 하는 자동화재탐지설비 감지기 종류는?",
    "1명의 안전관리자가 동일 공장 구내에 있는 옥내저장소 2개동과 일반취급소 1개동을 중복 선임할 수 있습니까?",
    "위험물안전관리자 퇴사 시 후임자를 선임해야 하는 법정 기한과 대리자 지정 기간은 며칠입니까?",
    "옥외저장탱크의 노후된 밸브와 펌프를 동일 사양 신품으로 1:1 교체 시 변경허가 대상입니까?",
    "경매로 위험물 옥내탱크저장소를 낙찰받은 자가 소방서에 지위승계를 신고해야 하는 기한은?",
    "위험물 예방규정을 정하여 소방서장에게 제출해야 하는 제조소등의 규모 기준은?",
    "제조소등의 정기점검 대상 시설과 점검기록 보존 기간은 몇 년입니까?",

    # 7. 추가 심층 기술 및 실무 기준 (10문항 -> 총 100문항 완성)
    "자연발화성 및 금수성물질(제3류)인 칼륨 화재 시 물소화설비를 사용할 수 있습니까?",
    "인화성고체(제2류) 2,000kg을 옥외에 비가림 천막만 치고 저장하는 것이 허용됩니까?",
    "이동탱크저장소(탱크로리) 탱크 내부에 설치하는 방파판과 칸막이의 용량 분할 기준은?",
    "옥내저장소 바닥면적 기준은 제1석유류 보관 시 최대 몇 제곱미터까지 허가 가능합니까?",
    "주유취급소 주유공지의 바닥 포장 재료와 배수구 유분리장치 설치 기준은?",
    "지하저장탱크 상부에 덮어야 하는 콘크리트 슬래브 두께 기준은 몇 cm 이상입니까?",
    "위험물 취급설비에 설치하는 긴급차단밸브는 어떤 비상 상황에 자동 차단되어야 합니까?",
    "제조소등에 설치하는 가연성 증기 누설 감지 경보설비의 설치 위치 기준은?",
    "위험물안전관리자를 선임한 후 소방서에 신고해야 하는 법정 기한은 며칠 이내입니까?",
    "위험물 운송자 자격증 없이 이동탱크저장소를 운전하다 적발된 경우 벌칙은 얼마입니까?"
]

print(f"Total test questions prepared: {len(QUESTIONS)}")

# 평가 함수: 사례집 서식 준수도 채점
def evaluate_response(user_q, resp_text):
    score = 0
    feedback_reasons = []

    # 1. 단정적 결론 검사 (30점)
    # "답 :" 또는 "답:" 또는 첫 문단에 결론이 명확한가?
    has_answer_prefix = bool(re.search(r"답\s*[:：]", resp_text))
    # 단정적 판정 단어 존재 여부
    definitive_words = ["허용", "불가", "위법", "적법", "처벌", "배", "해당", "아니", "확보", "인정", "취소", "벌금", "과태료", "면제", "이격", "초과", "미만", "이상"]
    has_definitive_word = any(w in resp_text[:150] for w in definitive_words)

    if has_answer_prefix and has_definitive_word:
        score += 30
    elif has_answer_prefix or has_definitive_word:
        score += 15
        feedback_reasons.append("결론 접두어('답 :') 또는 단정적 단어 부분 누락")
    else:
        feedback_reasons.append("단정적 1줄 결론('답 : ...') 미기재")

    # 2. 4단계 서식 구조 준수 검사 (25점)
    sections = [
        bool(re.search(r"【\s*회신\s*요지", resp_text) or "회신" in resp_text[:200] or "결론" in resp_text[:200]),
        bool(re.search(r"【\s*상세\s*이유", resp_text) or "상세 이유" in resp_text or "법적 해석" in resp_text),
        bool(re.search(r"【\s*관련\s*법령", resp_text) or "관련 법령" in resp_text or "적용 법조" in resp_text),
        bool(re.search(r"【\s*실무\s*유의사항", resp_text) or "참고자료" in resp_text or "처벌" in resp_text or "벌칙" in resp_text)
    ]
    matched_sections = sum(sections)
    if matched_sections >= 4:
        score += 25
    elif matched_sections == 3:
        score += 18
        feedback_reasons.append(f"4단계 섹션 중 일부 누락 ({matched_sections}/4)")
    elif matched_sections == 2:
        score += 10
        feedback_reasons.append(f"서식 구조 미흡 ({matched_sections}/4)")
    else:
        feedback_reasons.append("사례집 4단계 표준 구조 미준수")

    # 3. 구체적 법령 인용도 검사 (25점)
    statute_matches = re.findall(r"(위험물안전관리법|시행령|시행규칙|별표|조례|제\d+조|별표\s*\d+)", resp_text)
    if len(statute_matches) >= 3:
        score += 25
    elif len(statute_matches) >= 1:
        score += 15
        feedback_reasons.append("구체적 조문/별표 인용 부족")
    else:
        feedback_reasons.append("법적 근거(조문/별표) 미인용")

    # 4. 회피 및 두루뭉술 표현 배제 검사 (20점)
    vague_patterns = [
        r"사안에\s*따라\s*다를\s*수",
        r"검토가\s*필요합니다",
        r"판단하기\s*어렵습니다",
        r"소방서에\s*문의하시기\s*바랍니다$", # 결론 없이 소방서 문의로 끝나는 경우
        r"가능성이\s*있습니다",
        r"추정됩니다"
    ]
    has_vague = any(re.search(p, resp_text) for p in vague_patterns)
    if not has_vague:
        score += 20
    else:
        score += 5
        feedback_reasons.append("회피성·두루뭉술한 표현 포함 ('사안에 따라', '검토 필요' 등)")

    # 등급 판정
    if score >= 85:
        grade = "PASS" # 사용자가 원하는 완벽한 사례집 스타일
    elif score >= 70:
        grade = "PARTIAL" # 대체로 양호하나 일부 디테일 보완 필요
    else:
        grade = "FAIL" # 스타일 미달

    return {
        "score": score,
        "grade": grade,
        "feedback": feedback_reasons
    }

# 100회 실행 함수
def run_benchmark():
    bot = HazmatChatbot()
    results = []

    print(f"Starting 100 Q&A benchmark simulation...")
    start_total = time.time()

    def process_item(idx, q):
        t0 = time.time()
        try:
            res = bot.ask_with_meta(q)
            resp_text = res.get("response", "")
            elapsed = time.time() - t0
            eval_res = evaluate_response(q, resp_text)
            return {
                "index": idx + 1,
                "question": q,
                "response": resp_text,
                "score": eval_res["score"],
                "grade": eval_res["grade"],
                "feedback": eval_res["feedback"],
                "elapsed": round(elapsed, 2),
                "model_used": res.get("model_used")
            }
        except Exception as e:
            return {
                "index": idx + 1,
                "question": q,
                "response": f"ERROR: {str(e)}",
                "score": 0,
                "grade": "FAIL",
                "feedback": [f"호출 오류: {str(e)}"],
                "elapsed": 0,
                "model_used": "error"
            }

    # ThreadPoolExecutor로 8개 스레드 동시 처리 (속도 최적화)
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_idx = {executor.submit(process_item, idx, q): idx for idx, q in enumerate(QUESTIONS)}
        for future in as_completed(future_to_idx):
            r = future.result()
            results.append(r)
            if len(results) % 20 == 0 or len(results) == 100:
                print(f"Processed {len(results)}/100 items...")

    results.sort(key=lambda x: x["index"])
    total_time = round(time.time() - start_total, 1)

    # 통계 계산
    pass_count = sum(1 for r in results if r["grade"] == "PASS")
    partial_count = sum(1 for r in results if r["grade"] == "PARTIAL")
    fail_count = sum(1 for r in results if r["grade"] == "FAIL")

    pass_rate = round(pass_count / len(results) * 100, 1)
    partial_rate = round(partial_count / len(results) * 100, 1)
    fail_rate = round(fail_count / len(results) * 100, 1)

    # 피드백 사유 빈도 집계
    feedback_counter = {}
    for r in results:
        for f in r["feedback"]:
            feedback_counter[f] = feedback_counter.get(f, 0) + 1

    summary = {
        "total_count": len(results),
        "total_time_seconds": total_time,
        "pass_count": pass_count,
        "pass_rate_percent": pass_rate,
        "partial_count": partial_count,
        "partial_rate_percent": partial_rate,
        "fail_count": fail_count,
        "fail_rate_percent": fail_rate,
        "common_issues": feedback_counter,
        "detailed_results": results
    }

    with open("data/benchmark_100_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "="*50)
    print(f"100회 벤치마크 완료! (총 소요시간: {total_time}초)")
    print(f"▶ 완벽 부합 (PASS): {pass_count}개 ({pass_rate}%)")
    print(f"▶ 부분 부합 (PARTIAL): {partial_count}개 ({partial_rate}%)")
    print(f"▶ 스타일 미흡 (FAIL): {fail_count}개 ({fail_rate}%)")
    print("="*50)
    print("주요 감점 및 부족 사유 통계:")
    for issue, cnt in sorted(feedback_counter.items(), key=lambda x: x[1], reverse=True):
        print(f" - {issue}: {cnt}회 ({round(cnt/len(results)*100, 1)}%)")

if __name__ == "__main__":
    run_benchmark()
