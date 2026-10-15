"""
services/checklist_service.py
위험물제조소등 유형별 소방특사경 단속 체크리스트 데이터 및 보고서 생성 서비스
- 6대 핵심 시설 유형(제조소/일반취급소, 옥내외저장소, 옥외탱크, 이동탱크, 주유취급소, 무허가장소)
- 필수 징구 서류 목록, 4단계 실무 점검 항목, 적용 법조문, 법정 형량, 현장 채증 포인트 제공
"""
from typing import Dict, Any, List, Optional

CHECKLIST_FACILITY_TYPES = [
    {
        "id": "mfg_general",
        "name": "제조소 및 일반취급소",
        "badge": "bg-blue-500/20 text-blue-400 border-blue-500/30",
        "icon": "factory",
        "target_desc": "위험물 제조공장, 도장부스, 세정조, 가열로, 화학 반응기 설치 사업장",
        "required_documents": [
            {"id": "doc_mfg_1", "name": "완공검사필증 (설치허가증 및 변경허가증 사본)", "desc": "허가 품명, 최대수량, 지정수량 배수 일치 확인", "critical": True},
            {"id": "doc_mfg_2", "name": "위험물안전관리자 선임 신고필증 및 자격증/실무교육 이수증", "desc": "선임 신고 여부 및 2년 주기 실무교육 이수 여부", "critical": True},
            {"id": "doc_mfg_3", "name": "위험물제조소등 정기점검기록부 (최근 3년 보관분)", "desc": "연 1회 이상 정기점검 실시 및 기록 보존 확인", "critical": False},
            {"id": "doc_mfg_4", "name": "위험물 품명별 수불관리대장 및 원자재 입출고 세금계산서·거래명세표", "desc": "최근 1년간 실제 입고량과 일일 최대 취급량 대조", "critical": True},
            {"id": "doc_mfg_5", "name": "취급 화학물질 MSDS(물질안전보건자료) 및 시험성적서", "desc": "인화점, 성분 함유량, 품명 분류 적합성 검증", "critical": False},
            {"id": "doc_mfg_6", "name": "배관·계장도(P&ID) 및 공정도(위치·구조·설비 도면)", "desc": "허가 도면과 현장 설비의 일치 여부 비교", "critical": False}
        ],
        "steps": [
            {
                "step_no": 1,
                "step_name": "1단계: 외곽 및 공지 점검",
                "items": [
                    {
                        "id": "mfg_s1_1",
                        "title": "보유공지 내 제품·파렛트·원자재 무단 적치",
                        "check_point": "제조소 외벽으로부터 배수에 따른 법정 공지(3m~15m) 내 장애물 및 가연물 적치 여부 확인",
                        "law": "위험물안전관리법 제5조제3항 / 시행규칙 별표 4",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "건물 외벽과 파렛트 사이 거리 측정(줄자) 사진 및 원경·근경 사진 채증"
                    },
                    {
                        "id": "mfg_s1_2",
                        "title": "허가받지 않은 가설건축물(천막, 비가림 차양) 무단 증축",
                        "check_point": "허가 도면 외벽에 파이프/천막을 덧대어 건조실, 원자재 창고로 확장 사용 여부",
                        "law": "위험물안전관리법 제6조제1항 (무허가 변경)",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금 (허가취소·사용정지 대상)",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "설치허가도면 대비 불법 증축 부분 외관 사진 및 내부 적치물 촬영"
                    },
                    {
                        "id": "mfg_s1_3",
                        "title": "제조소 표지 및 위험물 주의사항 게시판 미부착·훼손",
                        "check_point": "출입구의 백색 바탕 흑색 문자 표지, 화기엄금/물기엄금 게시판 규격 및 부착 상태",
                        "law": "위험물안전관리법 시행규칙 별표 4",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "출입구 전경 및 게시판 미부착 상태 촬영"
                    }
                ]
            },
            {
                "step_no": 2,
                "step_name": "2단계: 건축물 구조 및 방화시설 점검",
                "items": [
                    {
                        "id": "mfg_s2_1",
                        "title": "자동폐쇄식 방화문 개방 고정(쐐기·고임목 설치) 또는 훼손",
                        "check_point": "연소확대 방지를 위한 갑종방화문에 고임목을 괴어 열어두거나 도어클로저를 파손한 행위",
                        "law": "위험물안전관리법 시행규칙 별표 4",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "방화문 하부 쐐기(고임목) 삽입 상태 근접 촬영"
                    },
                    {
                        "id": "mfg_s2_2",
                        "title": "가연성 증기 체류 장소에 비방폭형 전기·모터 설비 설치",
                        "check_point": "제4류 위험물 취급실 내 환풍기, 스위치, 조명등이 내압방폭/본질안전 방폭 구조인지 확인",
                        "law": "위험물안전관리법 시행규칙 별표 4 Ⅰ. 제11호",
                        "penalty": "시정명령 및 1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "일반 가정용 환풍기/비방폭 조명등 명판 접사 촬영"
                    },
                    {
                        "id": "mfg_s2_3",
                        "title": "바닥 유출방지턱 미설치 및 집유설비 배수밸브 방치",
                        "check_point": "위험물이 외부로 흘러나가지 않도록 하는 턱 높이 미달 또는 유분리조 배수구 개방",
                        "law": "위험물안전관리법 시행규칙 별표 4 Ⅰ. 제9호",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "바닥 턱 결손 부위 및 외부 유출 흔적 촬영"
                    }
                ]
            },
            {
                "step_no": 3,
                "step_name": "3단계: 제조·취급 공정 및 저장 실태 점검",
                "items": [
                    {
                        "id": "mfg_s3_1",
                        "title": "허가받지 않은 반응기, 교반기, 열교환기, 배관 임의 증설",
                        "check_point": "P&ID 도면과 대조하여 허가받지 않은 생산설비·배관을 증설하여 가동하는 행위",
                        "law": "위험물안전관리법 제6조제1항 (무허가 변경)",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "증설된 설비 명판, 배관 연결 상태 및 작동 중인 현장 영상 촬영"
                    },
                    {
                        "id": "mfg_s3_2",
                        "title": "허가 품명 외 타 품명 위험물 무단 취급",
                        "check_point": "완공검사필증에 등재되지 않은 이종 위험물(예: 4류 1석유류만 허가받고 2석유류/특수인화물 취급)",
                        "law": "위험물안전관리법 제5조제1항",
                        "penalty": "3년 이하의 징역 또는 3천만원 이하의 벌금",
                        "penalty_level": "criminal_3y",
                        "evidence_point": "용기 표면 라벨의 화학물질명 접사 및 입고 명세표 확보"
                    },
                    {
                        "id": "mfg_s3_3",
                        "title": "작업장 바닥에 허가량 초과 20L 말통/드럼 무단 야적",
                        "check_point": "당일 소요량을 초과하여 공장 바닥에 다량의 위험물 용기를 저장소처럼 쌓아둔 행위",
                        "law": "위험물안전관리법 제5조제1항 (무허가 저장)",
                        "penalty": "3년 이하의 징역 또는 3천만원 이하의 벌금 (1.0배 이상 시)",
                        "penalty_level": "criminal_3y",
                        "evidence_point": "적치된 말통/드럼 전수 계수 사진 및 총 수량 계산서 첨부"
                    }
                ]
            },
            {
                "step_no": 4,
                "step_name": "4단계: 안전관리자 및 소화설비 점검",
                "items": [
                    {
                        "id": "mfg_s4_1",
                        "title": "위험물안전관리자 미선임 (퇴직일로부터 30일 초과)",
                        "check_point": "전임 안전관리자 퇴사 후 30일 이내 후임자를 선임하지 않은 상태",
                        "law": "위험물안전관리법 제15조제3항",
                        "penalty": "1,500만원 이하의 벌금",
                        "penalty_level": "criminal_fine_1500",
                        "evidence_point": "인사기록 카드, 4대보험 상실신고서, 소방서 선임이력 조회서"
                    },
                    {
                        "id": "mfg_s4_2",
                        "title": "안전관리자 현장 부재 시 대리자 미지정",
                        "check_point": "안전관리자 휴가/출장 중 대리자를 서면 지정하지 않고 위험물 제조시설을 가동",
                        "law": "위험물안전관리법 제15조제6항",
                        "penalty": "500만원 이하의 과태료",
                        "penalty_level": "fine_500",
                        "evidence_point": "당일 근무일지 및 공장 가동 중인 작업자 진술서"
                    },
                    {
                        "id": "mfg_s4_3",
                        "title": "소화설비 가압송수장치(펌프) 밸브 폐쇄 또는 전원 차단",
                        "check_point": "옥내소화전 또는 스프링클러 제어반 주경종/펌프스위치 정지 상태",
                        "law": "소방시설법 제12조 / 위험물안전관리법 별표 17",
                        "penalty": "5년 이하의 징역 또는 5천만원 이하의 벌금",
                        "penalty_level": "criminal_5y",
                        "evidence_point": "수신기 정지 램프 점등 및 밸브 폐쇄 상태 계측 사진"
                    }
                ]
            }
        ]
    },
    {
        "id": "indoor_outdoor_storage",
        "name": "옥내 및 옥외저장소",
        "badge": "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
        "icon": "warehouse",
        "target_desc": "위험물 전용 창고 건물, 야외 위험물 전용 야적 저장소",
        "required_documents": [
            {"id": "doc_ios_1", "name": "완공검사필증 (허가 배수 및 보관 품명 명시)", "desc": "허가 배수와 실제 적치 배수 대조 확인", "critical": True},
            {"id": "doc_ios_2", "name": "위험물안전관리자 선임 신고필증", "desc": "선임 유효기간 및 상주 여부", "critical": True},
            {"id": "doc_ios_3", "name": "위험물 정기점검기록표 (연 1회 실시분)", "desc": "자체점검 실시 결과 및 이상유무", "critical": False},
            {"id": "doc_ios_4", "name": "창고 입출고 수불대장 및 ERP 재고 실사표", "desc": "당일 실제 보관 수량 및 월별 최대치 확인", "critical": True},
            {"id": "doc_ios_5", "name": "운반용기 성능시험성적서 (KFI 검정마크)", "desc": "드럼/IBC탱크 용기 검정 여부", "critical": False}
        ],
        "steps": [
            {
                "step_no": 1,
                "step_name": "1단계: 보유공지 및 창고 외곽",
                "items": [
                    {
                        "id": "ios_s1_1",
                        "title": "법정 보유공지 내 물건 적치",
                        "check_point": "저장 배수별 법정 공지(5m, 3m 등)에 파렛트, 공드럼, 폐박스를 쌓아둔 행위",
                        "law": "위험물안전관리법 시행규칙 별표 5 / 별표 11",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "창고 벽체와 물건 사이 거리 측정 사진"
                    },
                    {
                        "id": "ios_s1_2",
                        "title": "채광·환기·배출설비 인화방지망 훼손",
                        "check_point": "자연배출구 또는 환기구의 구리망(가는 눈의 철망) 파손 및 기름때 막힘",
                        "law": "위험물안전관리법 시행규칙 별표 5",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "환기구 망 훼손 접사 촬영"
                    }
                ]
            },
            {
                "step_no": 2,
                "step_name": "2단계: 저장 수량 및 혼재 기준",
                "items": [
                    {
                        "id": "ios_s2_1",
                        "title": "허가 지정수량 배수 초과 저장",
                        "check_point": "허가받은 배수(예: 20배)를 초과하여 실제 30배 이상 보관하는 행위",
                        "law": "위험물안전관리법 제6조제1항 (무허가 변경)",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "창고 내 파렛트별 수량 전수 계수표 및 ERP 재고표"
                    },
                    {
                        "id": "ios_s2_2",
                        "title": "류별 혼재 기준 위반 병치 보관",
                        "check_point": "제4류(인화성액체)와 제1류(산화성고체) 또는 제6류(산화성액체)를 동일 실내에 보관",
                        "law": "위험물안전관리법 시행규칙 별표 19",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "이종 류별 라벨이 함께 나오도록 적치 상태 촬영"
                    },
                    {
                        "id": "ios_s2_3",
                        "title": "용기 적재 높이 기준 초과",
                        "check_point": "기계하역 구조가 아닌 경우 3m 초과, 겹쳐쌓기 규격용기 4m 초과 적재",
                        "law": "위험물안전관리법 시행규칙 별표 5",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "레이저 거리측정기 또는 측정자로 단차 높이 계측 사진"
                    }
                ]
            },
            {
                "step_no": 3,
                "step_name": "3단계: 용기 규격 및 통로",
                "items": [
                    {
                        "id": "ios_s3_1",
                        "title": "위험물 운반용기 표시·GHS 경고표지 누락",
                        "check_point": "위험물 품명, 화학명, 수량, 수용성 여부, 주의사항 경고라벨 미부착 용기 유통",
                        "law": "위험물안전관리법 제20조제1항",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "라벨이 없는 백지 용기 또는 훼손된 라벨 접사"
                    },
                    {
                        "id": "ios_s3_2",
                        "title": "창고 내 비상점검 통로(0.6m) 미확보",
                        "check_point": "출입구에서 안쪽까지 점검 및 피난을 위한 0.6m 이상의 통로가 막힌 상태",
                        "law": "위험물안전관리법 시행규칙 별표 5",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "통로 없이 빽빽하게 채워진 창고 내부 전경 촬영"
                    }
                ]
            }
        ]
    },
    {
        "id": "outdoor_tank",
        "name": "옥외탱크저장소",
        "badge": "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
        "icon": "cylinder",
        "target_desc": "대형 옥외 유류 저장탱크, 위험물 화학탱크",
        "required_documents": [
            {"id": "doc_ot_1", "name": "탱크 완공검사필증 및 구조안전점검 결과서", "desc": "탱크 용량 및 기초 지반 침하 여부 확인", "critical": True},
            {"id": "doc_ot_2", "name": "방유제 용량 계산서 및 탱크 용적 도면", "desc": "탱크 용량의 110% 이상 유효용량 충족 여부", "critical": True},
            {"id": "doc_ot_3", "name": "정기점검 및 정밀안전진단 기록부", "desc": "배관 수압시험 및 판두께 측정 기록", "critical": False},
            {"id": "doc_ot_4", "name": "포소화설비 약제 검정서 및 방출시험 보고서", "desc": "고정식 포방출구 약제 상태 및 혼합비 확인", "critical": False}
        ],
        "steps": [
            {
                "step_no": 1,
                "step_name": "1단계: 방유제(Dike) 관리 실태",
                "items": [
                    {
                        "id": "ot_s1_1",
                        "title": "방유제 배수밸브 개방 상태 방치",
                        "check_point": "평상시 '닫힘(잠금)' 상태여야 할 방유제 빗물 배수밸브를 열어둔 행위",
                        "law": "위험물안전관리법 시행규칙 별표 6 제17호",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "배수밸브가 열려 있는 상태 및 밸브 주변 접사 촬영"
                    },
                    {
                        "id": "ot_s1_2",
                        "title": "방유제 내부에 가연물·파렛트·드럼통 무단 적치",
                        "check_point": "누유 시 화재 확산 방지 목적의 방유제 내부 공간에 물건을 쌓아둔 행위",
                        "law": "위험물안전관리법 시행규칙 별표 6",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "방유제 내부 바닥에 적치된 물건 전경 촬영"
                    },
                    {
                        "id": "ot_s1_3",
                        "title": "방유제 콘크리트 균열 및 배관 관통부 틈새 미마감",
                        "check_point": "누유 시 위험물이 외부로 새어나갈 수 있는 크랙 또는 배관 관통부 방화충전 미흡",
                        "law": "위험물안전관리법 시행규칙 별표 6",
                        "penalty": "시정명령 및 1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "방유제 외벽 균열 부위 자 대고 촬영"
                    }
                ]
            },
            {
                "step_no": 2,
                "step_name": "2단계: 탱크 본체 및 부속배관",
                "items": [
                    {
                        "id": "ot_s2_1",
                        "title": "통기관 화염방지망(인화방지망) 파손 또는 누락",
                        "check_point": "무변통기관 끝단 동망(구리선망) 파손으로 외부 화염 역류 위험 상태",
                        "law": "위험물안전관리법 시행규칙 별표 6",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "벤트관 말단 방화망 상태 근접 촬영"
                    },
                    {
                        "id": "ot_s2_2",
                        "title": "정전기 제거 접지설비(본딩) 단선 및 접지저항 불량",
                        "check_point": "탱크와 배관 간 접지선 체결 볼트 탈락 또는 저항값 100Ω 초과",
                        "law": "위험물안전관리법 시행규칙 별표 4 / 별표 6",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "접지 단선 부위 및 접지저항계 측정값 표시창 촬영"
                    },
                    {
                        "id": "ot_s2_3",
                        "title": "탱크 주입구·맨홀·배관 연결부 유류 누설 흔적",
                        "check_point": "가스켓 부식 등으로 플랜지 연결부에서 기름이 흘러내린 자국",
                        "law": "위험물안전관리법 제5조제3항",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "누유 부위 및 바닥 오염 상태 사진 채증"
                    }
                ]
            }
        ]
    },
    {
        "id": "mobile_tank",
        "name": "이동탱크저장소 (탱크로리)",
        "badge": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
        "icon": "truck",
        "target_desc": "유류 탱크로리, 이동주유차량 (특장차)",
        "required_documents": [
            {"id": "doc_mt_1", "name": "이동탱크저장소 완공검사필증 (차량등록번호 대조)", "desc": "허가 차량번호 및 최대 적재용량 일치 확인", "critical": True},
            {"id": "doc_mt_2", "name": "위험물운송자증 (또는 국가기술자격수첩 + 실무교육증)", "desc": "운전자의 운송자 자격 취득 여부", "critical": True},
            {"id": "doc_mt_3", "name": "상치장소(허가된 전용 차고지) 증명 서류", "desc": "허가받은 주차장 위치 확인", "critical": True},
            {"id": "doc_mt_4", "name": "위험물운송장 (화물 운송 시 비치의무)", "desc": "품명, 수량, 출발지, 목적지 일치 여부", "critical": True},
            {"id": "doc_mt_5", "name": "정기점검기록부 (차량 내 비치본)", "desc": "최근 1년 이내 정기점검 실시 기록", "critical": False}
        ],
        "steps": [
            {
                "step_no": 1,
                "step_name": "1단계: 상치장소 및 운전자 자격",
                "items": [
                    {
                        "id": "mt_s1_1",
                        "title": "상치장소 위반 야간 불법 밤샘주차",
                        "check_point": "허가받은 상치장소가 아닌 주택가, 이면도로, 나대지에 밤샘 주차한 행위",
                        "law": "위험물안전관리법 제5조제1항",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "야간 주차 위치(도로 표지판, 지번), 차량 번호판, 주변 배경 사진"
                    },
                    {
                        "id": "mt_s1_2",
                        "title": "무자격 위험물 운송자 운전",
                        "check_point": "위험물운송자 자격을 취득하지 않은 자가 탱크로리를 운전하여 운송한 행위",
                        "law": "위험물안전관리법 제20조제2항",
                        "penalty": "1,500만원 이하의 벌금 (운송자 미취득 시)",
                        "penalty_level": "criminal_fine_1500",
                        "evidence_point": "운전자 신분증 및 안전원 자격 전산 조회 결과 캡처"
                    },
                    {
                        "id": "mt_s1_3",
                        "title": "위험물운송장 미비치 또는 허위 기재",
                        "check_point": "운송 중 위험물운송장을 휴대하지 않거나 수량·품명을 거짓으로 작성",
                        "law": "위험물안전관리법 제20조제3항",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "운전석 대시보드 수색 사진 및 송장 부존재 확인서"
                    }
                ]
            },
            {
                "step_no": 2,
                "step_name": "2단계: 탱크 구조 및 안전장비",
                "items": [
                    {
                        "id": "mt_s2_1",
                        "title": "격실 용량(최대 4,000L 이하) 위반 또는 방파판 훼손",
                        "check_point": "격실 간 칸막이 임의 철거 또는 방파판 탈락 상태로 운행",
                        "law": "위험물안전관리법 시행규칙 별표 10",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "맨홀 내부 격실 구조 및 용량 표시판 촬영"
                    },
                    {
                        "id": "mt_s2_2",
                        "title": "비상밸브 차단장치(레버/와이어) 작동 불량",
                        "check_point": "비상 시 유류 누출을 차단하는 비상레버의 고착 또는 와이어 절단 방치",
                        "law": "위험물안전관리법 시행규칙 별표 10",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "비상레버 조작 불능 상태 영상 또는 절단 부위 사진"
                    },
                    {
                        "id": "mt_s2_3",
                        "title": "자동차용 분말소화기 미비치 또는 압력 저하",
                        "check_point": "규격 분말소화기 2개 이상 미비치 또는 지침 지시압력 미달(빨간색 영역)",
                        "law": "위험물안전관리법 시행규칙 별표 10",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "차량 측면 소화기 보관함 및 압력게이지 지침 접사 촬영"
                    }
                ]
            }
        ]
    },
    {
        "id": "gas_station",
        "name": "주유취급소",
        "badge": "bg-amber-500/20 text-amber-400 border-amber-500/30",
        "icon": "fuel",
        "target_desc": "일반 주유소, 셀프 주유소, 고정식 급유소",
        "required_documents": [
            {"id": "doc_gs_1", "name": "주유취급소 완공검사필증 (부대용도 허가 여부)", "desc": "허가된 부대업무(세차기, 편의점 등) 범위 확인", "critical": True},
            {"id": "doc_gs_2", "name": "위험물안전관리자 선임 신고필증 및 상주 확인서", "desc": "영업시간 중 안전관리자 상주 근무 여부", "critical": True},
            {"id": "doc_gs_3", "name": "지하저장탱크 누설검사기록부 (기밀시험)", "desc": "정기 누설검사(3년/5년 주기) 이행 여부", "critical": False},
            {"id": "doc_gs_4", "name": "POS 판매원장 및 일일 입출고 원장", "desc": "말통 판매 내역 및 이상 출고 확인", "critical": False}
        ],
        "steps": [
            {
                "step_no": 1,
                "step_name": "1단계: 주유공지 및 부대시설",
                "items": [
                    {
                        "id": "gs_s1_1",
                        "title": "주유공지 내 무단 가설물 축조 또는 잡품 적치",
                        "check_point": "차량 진출입 및 피난을 위한 주유공지에 컨테이너, 천막, 타이어를 무단 적치",
                        "law": "위험물안전관리법 제6조제1항 및 시행규칙 별표 13",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "주유기 주변 적치된 장애물 및 공지 침범 사진"
                    },
                    {
                        "id": "gs_s1_2",
                        "title": "허가받지 않은 부대업무 영위 (무단 차량 정비 등)",
                        "check_point": "허가받지 않고 주유소 부지 내에서 오일교환, 타이어 교체 등 무단 카센터 영업",
                        "law": "위험물안전관리법 제6조제1항",
                        "penalty": "1년 이하의 징역 또는 1천만원 이하의 벌금",
                        "penalty_level": "criminal_1y",
                        "evidence_point": "정비 장비(리프트 등) 및 정비 작업 현장 사진"
                    },
                    {
                        "id": "gs_s1_3",
                        "title": "주유소 방화벽 임의 개구부 뚫음 및 훼손",
                        "check_point": "인접 건물과의 연소방지를 위한 내화 방화벽을 뚫어 출입구로 개조한 행위",
                        "law": "위험물안전관리법 시행규칙 별표 13",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "방화벽 관통 및 뚫린 개구부 사진"
                    }
                ]
            },
            {
                "step_no": 2,
                "step_name": "2단계: 주유설비 및 고객 주유 안전",
                "items": [
                    {
                        "id": "gs_s2_1",
                        "title": "셀프주유소 고객의 플라스틱 말통 무단 주유 방치",
                        "check_point": "고객이 셀프주유기에서 자동차 연료탱크 외 말통에 직접 휘발유를 주유하도록 방치",
                        "law": "위험물안전관리법 시행규칙 별표 13",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "CCTV 녹화 영상 확보 및 말통 주유 현장 사진"
                    },
                    {
                        "id": "gs_s2_2",
                        "title": "주유노즐 정전기 방지 패드 파손 및 접지 불량",
                        "check_point": "셀프주유기 전면 정전기 패드 탈락 또는 접지선 단선",
                        "law": "위험물안전관리법 시행규칙 별표 13",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "정전기 패드 훼손 상태 접사"
                    },
                    {
                        "id": "gs_s2_3",
                        "title": "야간 영업 중 안전관리자 미상주 (셀프주유소)",
                        "check_point": "24시간 셀프주유소 야간 시간대에 감시원 또는 안전관리자가 사무실을 비운 상태",
                        "law": "위험물안전관리법 제15조",
                        "penalty": "1,500만원 이하의 벌금",
                        "penalty_level": "criminal_fine_1500",
                        "evidence_point": "야간 현장 방문 시 사무실 부재 확인서 및 CCTV 확인"
                    }
                ]
            }
        ]
    },
    {
        "id": "unauthorized_storage",
        "name": "무허가 저장·취급 (기획단속 1순위)",
        "badge": "bg-rose-500/20 text-rose-400 border-rose-500/30",
        "icon": "alert-triangle",
        "target_desc": "공장 마당, 야외 나대지, 무허가 창고, 비닐하우스 등 지정수량 이상 적치 장소",
        "required_documents": [
            {"id": "doc_unauth_1", "name": "사업자등록증 및 토지·건물 등기부등본(또는 임대차계약서)", "desc": "불법 적치 행위자 및 토지 소유주/임차인 책임 소재 규명", "critical": True},
            {"id": "doc_unauth_2", "name": "위험물 구매 세금계산서, 거래명세표, 계근표", "desc": "입고 일자, 구매 품명, 실구매량 확인", "critical": True},
            {"id": "doc_unauth_3", "name": "물품 납품처 출하전표 및 ERP 원장", "desc": "저장 기간 및 상습적 저장·취급 여부 입증", "critical": True},
            {"id": "doc_unauth_4", "name": "취급 물질 MSDS (인화점·함유량 증빙)", "desc": "지정수량 기준치 적용을 위한 물질 분석표", "critical": True}
        ],
        "steps": [
            {
                "step_no": 1,
                "step_name": "1단계: 수량 산정 및 위법 배수 확정",
                "items": [
                    {
                        "id": "unauth_s1_1",
                        "title": "지정수량 1.0배 이상 무허가 저장·취급 (형사입건)",
                        "check_point": "허가받지 않은 장소에 지정수량 1.0배 이상의 위험물을 저장 또는 취급한 행위",
                        "law": "위험물안전관리법 제5조제1항",
                        "penalty": "3년 이하의 징역 또는 3천만원 이하의 벌금 (형사처벌)",
                        "penalty_level": "criminal_3y",
                        "evidence_point": "적치된 드럼/말통/IBC탱크 전수 계수 사진, 품명 라벨, 계산기 배수 산출표"
                    },
                    {
                        "id": "unauth_s1_2",
                        "title": "지정수량 0.2배 이상 ~ 1.0배 미만 조례 위반 저장",
                        "check_point": "시·도 조례(경기도 위험물 안전관리 조례 등) 기준 소량위험물 저장·취급 기준 위반",
                        "law": "시·도 위험물 안전관리 조례 (법 제5조제4항)",
                        "penalty": "200만원 이하의 과태료",
                        "penalty_level": "fine_200",
                        "evidence_point": "조례 기준 0.2배 충족 수량 계수표 및 현장 사진"
                    }
                ]
            },
            {
                "step_no": 2,
                "step_name": "2단계: 불법 취급 행위 및 상태",
                "items": [
                    {
                        "id": "unauth_s2_1",
                        "title": "야외 노상 무단 소분·주입·가열·혼합 취급",
                        "check_point": "안전설비 없는 마당이나 도로변에서 드럼 펌프로 말통에 유류를 소분·주입하는 행위",
                        "law": "위험물안전관리법 제5조제1항",
                        "penalty": "3년 이하의 징역 또는 3천만원 이하의 벌금",
                        "penalty_level": "criminal_3y",
                        "evidence_point": "소분 작업에 사용된 주입건, 이동식 펌프, 흘린 기름 자국 촬영"
                    },
                    {
                        "id": "unauth_s2_2",
                        "title": "임시저장 승인(최대 90일) 미필 보관",
                        "check_point": "소방서장의 사전 임시저장 승인을 받지 않고 공사현장 등에 유류 방치",
                        "law": "위험물안전관리법 제5조제2항 단서",
                        "penalty": "3년 이하의 징역 또는 3천만원 이하의 벌금",
                        "penalty_level": "criminal_3y",
                        "evidence_point": "소방서 승인서 부존재 확인 및 공사현장 유류 보관 사진"
                    }
                ]
            },
            {
                "step_no": 3,
                "step_name": "3단계: 3대 핵심 물증 확보",
                "items": [
                    {
                        "id": "unauth_s3_1",
                        "title": "용기 표면 품명·UN번호·GHS 라벨 접사 채증",
                        "check_point": "물질을 특정할 수 있는 드럼/말통 표면의 라벨, UN 표시, 위험물 스티커 촬영",
                        "law": "형사소송법상 증거능력 확보",
                        "penalty": "위법 입증 핵심 물증",
                        "penalty_level": "evidence",
                        "evidence_point": "라벨 글자가 선명히 보이도록 초점 맞춘 고해상도 접사 사진"
                    },
                    {
                        "id": "unauth_s3_2",
                        "title": "현장 책임자 자인서(확인서) 및 임의제출동의서 징구",
                        "check_point": "위험물 보관 사실 및 인지 여부, 적치 기간을 명시한 자필 서명 확인서 확보",
                        "law": "특별사법경찰관 집무규칙",
                        "penalty": "피의자 신문 및 송치 서류 첨부",
                        "penalty_level": "evidence",
                        "evidence_point": "서명 날인된 확인서 원본 스캔/촬영"
                    }
                ]
            }
        ]
    }
]

class ChecklistService:
    @classmethod
    def get_all_facilities(cls) -> List[Dict[str, Any]]:
        """모든 시설 유형 요약 리스트 반환"""
        return [
            {
                "id": f["id"],
                "name": f["name"],
                "badge": f["badge"],
                "icon": f["icon"],
                "target_desc": f["target_desc"],
                "steps_count": len(f["steps"]),
                "items_count": sum(len(s["items"]) for s in f["steps"]),
                "docs_count": len(f["required_documents"])
            }
            for f in CHECKLIST_FACILITY_TYPES
        ]

    @classmethod
    def get_facility_checklist(cls, facility_id: str) -> Optional[Dict[str, Any]]:
        """특정 시설의 전체 체크리스트 반환"""
        for f in CHECKLIST_FACILITY_TYPES:
            if f["id"] == facility_id:
                return f
        return None

    @classmethod
    def generate_inspection_report(cls, facility_id: str, checked_violations: List[str], missing_docs: List[str], memo: str = "", biz_info: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        체크된 위반 항목 및 미비 서류를 기반으로 소방특사경 공식 단속보고서 자동 생성
        """
        facility = cls.get_facility_checklist(facility_id)
        if not facility:
            return {"error": "시설 유형을 찾을 수 없습니다."}

        biz_name = (biz_info or {}).get("biz_name") or "미상 사업장"
        location = (biz_info or {}).get("location") or "현장 미기재"
        inspector = (biz_info or {}).get("inspector") or "소방특별사법경찰관"

        violation_details = []
        highest_penalty = "위반 사항 없음"
        highest_level_rank = 0

        penalty_rank_map = {
            "criminal_5y": (5, "5년 이하의 징역 또는 5천만원 이하의 벌금"),
            "criminal_3y": (4, "3년 이하의 징역 또는 3천만원 이하의 벌금"),
            "criminal_1y": (3, "1년 이하의 징역 또는 1천만원 이하의 벌금"),
            "criminal_fine_1500": (2, "1,500만원 이하의 벌금"),
            "fine_500": (1, "500만원 이하의 과태료"),
            "fine_200": (1, "200만원 이하의 과태료"),
            "evidence": (0, "수사 채증 사항")
        }

        # Check item violations
        for step in facility["steps"]:
            for item in step["items"]:
                if item["id"] in checked_violations:
                    p_lvl = item.get("penalty_level", "fine_200")
                    rank, p_desc = penalty_rank_map.get(p_lvl, (0, item.get("penalty", "")))
                    if rank > highest_level_rank:
                        highest_level_rank = rank
                        highest_penalty = p_desc
                    
                    violation_details.append({
                        "id": item["id"],
                        "title": item["title"],
                        "law": item["law"],
                        "penalty": item["penalty"],
                        "evidence_point": item["evidence_point"]
                    })

        # Missing docs
        missing_doc_names = []
        for doc in facility["required_documents"]:
            if doc["id"] in missing_docs:
                missing_doc_names.append(doc["name"])

        # Format Text Report
        lines = []
        lines.append("=" * 60)
        lines.append("【소방특별사법경찰 위험물제조소등 현장단속 적발보고서】")
        lines.append("=" * 60)
        lines.append(f"• 단속 대상: {biz_name} ({facility['name']})")
        lines.append(f"• 현장 주소: {location}")
        lines.append(f"• 단속관: {inspector}")
        lines.append(f"• 최고 적용 형량: {highest_penalty}")
        lines.append(f"• 총 적발 위법 건수: {len(violation_details)}건")
        lines.append("-" * 60)

        if violation_details:
            lines.append("■ 적발된 위법 사실 및 법적 조치:")
            for idx, v in enumerate(violation_details, 1):
                lines.append(f" {idx}. {v['title']}")
                lines.append(f"    - 적용 법조: {v['law']}")
                lines.append(f"    - 처벌 규정: {v['penalty']}")
                lines.append(f"    - 채증 요령: {v['evidence_point']}")
        else:
            lines.append("■ 적발된 위법 사실: 특이 위반사항 없음 (적합)")

        if missing_doc_names:
            lines.append("-" * 60)
            lines.append("■ 현장 미제출 및 징구 필요 서류:")
            for d in missing_doc_names:
                lines.append(f"  • {d}")

        if memo.strip():
            lines.append("-" * 60)
            lines.append(f"■ 단속관 현장 특이사항 메모:\n{memo.strip()}")

        lines.append("=" * 60)
        lines.append("위와 같이 위험물안전관리법 위반 사실을 현장 확인 및 채증함.")

        full_text = "\n".join(lines)

        return {
            "facility_id": facility_id,
            "facility_name": facility["name"],
            "biz_name": biz_name,
            "location": location,
            "violations_count": len(violation_details),
            "highest_penalty": highest_penalty,
            "violation_details": violation_details,
            "missing_docs": missing_doc_names,
            "memo": memo,
            "report_text": full_text
        }
