"""
services/agent_model_manager.py
6대 전문 서브에이전트 및 메인 챗봇의 언어모델(LLM) 개별 설정 관리자
- 에이전트별 독립된 모델(Gemini, GPT-4o, GPT-4o-mini, Offline) 및 Temperature 배정
- JSON 영속화 및 원클릭 프리셋 지원
- 다중 LLM(OpenAI, Gemini) 통합 라우팅 및 연결 검증
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "agent_model_config.json")

# 지원 가능한 모델 레지스트리
SUPPORTED_MODELS = [
    {
        "id": "gpt-6.1-sol",
        "provider": "openai",
        "name": "GPT-6.1-sol",
        "tag": "OpenAI / 내 플랜 최신 플래그십",
        "badge": "bg-rose-500/20 text-rose-400 border-rose-500/30",
        "description": "사용자 OpenAI 플랜 사용. 최신 차세대 추론 엔진, 압도적인 법률 분석 및 고난도 수사 지휘에 최적"
    },
    {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "name": "GPT-4o-mini",
        "tag": "OpenAI / 내 플랜 알뜰형 (토큰절약 [권장])",
        "badge": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
        "description": "사용자 OpenAI 플랜 사용. 응답 속도가 가장 빠르고 토큰 소모가 극소량이라 플랜 한도 절약에 최적"
    },
    {
        "id": "gpt-4o",
        "provider": "openai",
        "name": "GPT-4o",
        "tag": "OpenAI / 내 플랜 고성능",
        "badge": "bg-purple-500/20 text-purple-400 border-purple-500/30",
        "description": "사용자 OpenAI 플랜 사용. 가장 뛰어난 추론 능력과 정밀한 법률 포섭 및 수사전략 지휘에 적합"
    },
    {
        "id": "gemini-3.8-flash",
        "provider": "gemini",
        "name": "Gemini 3.8 Flash",
        "tag": "Google / 별도 충전 필요 (비권장)",
        "badge": "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
        "description": "구글 AI Studio 별도 결제 필요. 크레딧 소진 시 402 에러 발생 (OpenAI 플랜과 무관)"
    },
    {
        "id": "gemini-2.5-flash",
        "provider": "gemini",
        "name": "Gemini 2.5 Flash",
        "tag": "Google / 차세대 초고속",
        "badge": "bg-sky-500/20 text-sky-400 border-sky-500/30",
        "description": "구글 최신 고속 모델, 방대한 컨텍스트 분석 및 화학 물질 감별에 우수"
    },
    {
        "id": "gemini-flash-latest",
        "provider": "gemini",
        "name": "Gemini Flash Latest",
        "tag": "Google / 플래시 최신판",
        "badge": "bg-blue-500/20 text-blue-400 border-blue-500/30",
        "description": "구글 Gemini 플래시 최신 버전 엔드포인트"
    },
    {
        "id": "gemini-pro-latest",
        "provider": "gemini",
        "name": "Gemini Pro Latest",
        "tag": "Google / 대용량 심층 추론",
        "badge": "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
        "description": "구글 최상위 프로 모델, 복잡한 연혁 법령 및 방대한 유권해석 검토에 적합"
    },
    {
        "id": "offline-heuristic",
        "provider": "offline",
        "name": "로컬 룰 엔진 (Offline)",
        "tag": "로컬 파이썬 / 무과금·독립",
        "badge": "bg-amber-500/20 text-amber-400 border-amber-500/30",
        "description": "외부 AI API 호출 없이 내장된 특사경 수사 룰 및 DB로 결정론적 판단"
    }
]

# 에이전트 목록 및 기본 모델 매핑 (Gemini 3.8 Flash 특화영역 + GPT 법리/수사 최적 하이브리드)
DEFAULT_CONFIG = {
    "calc_agent": {
        "model_id": "gemini-3.8-flash",
        "temperature": 0.1,
        "reasoning_effort": "medium",
        "max_tokens": 500,
        "note": "수량계산 & 위법판정관 [★Gemini 특화] (0.5초대 초고속 연산 & 지정수량 배수 정밀 산출)"
    },
    "infer_agent": {
        "model_id": "gemini-3.8-flash",
        "temperature": 0.3,
        "reasoning_effort": "high",
        "max_tokens": 650,
        "note": "미상물질 & 화학감별관 [★Gemini 특화] (방대한 화학 지식 & MSDS 인화점·성분 심층 역산)"
    },
    "procedure_agent": {
        "model_id": "gpt-4o-mini",
        "temperature": 0.1,
        "reasoning_effort": "low",
        "max_tokens": 500,
        "note": "단속절차 & 포렌식수사관 (GPT-4o-mini: 형사소송법 적법절차 체크 & 서식 정밀 출력)"
    },
    "history_agent": {
        "model_id": "gpt-6.1-sol",
        "temperature": 0.2,
        "reasoning_effort": "medium",
        "max_tokens": 750,
        "note": "연혁법령 & 부칙해석관 [★GPT 특화] (구 소방법 연혁 추적 & 부칙 제2조 심층 법리 분석)"
    },
    "public_agent": {
        "model_id": "gemini-3.8-flash",
        "temperature": 0.2,
        "reasoning_effort": "high",
        "max_tokens": 650,
        "note": "공공데이터 & 유권해석관 [★Gemini 특화] (100만 토큰 롱컨텍스트: 대용량 사업장 DB & 유권해석 매칭)"
    },
    "tactics_agent": {
        "model_id": "gpt-6.1-sol",
        "temperature": 0.3,
        "reasoning_effort": "medium",
        "max_tokens": 750,
        "note": "기획단속 & 변명차단관 [★GPT 특화] (3대 서류 입증, 피의자 궤변 논파 & 고난도 수사전략)"
    },
    "coordinator_agent": {
        "model_id": "gpt-6.1-sol",
        "temperature": 0.2,
        "reasoning_effort": "medium",
        "max_tokens": 800,
        "note": "합동작전 총괄 지휘본부장 [★GPT 특화] (6대 에이전트 의견 종합 및 최종 작전명령서 작성)"
    },
    "main_chatbot": {
        "model_id": "gpt-4o-mini",
        "temperature": 0.2,
        "reasoning_effort": "low",
        "max_tokens": 750,
        "note": "메인 법률상담 AI 비서 (GPT-4o-mini 기본: 상단 드롭다운으로 Gemini 3.8 Flash 원클릭 전환)"
    }
}

class AgentModelManager:
    _cached_config: Optional[Dict[str, Any]] = None

    @classmethod
    def get_supported_models(cls) -> List[Dict[str, Any]]:
        return SUPPORTED_MODELS

    @classmethod
    def get_api_key_status(cls) -> Dict[str, Any]:
        openai_key = os.getenv("OPENAI_API_KEY", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        return {
            "openai": {
                "configured": bool(openai_key and len(openai_key) > 10),
                "masked": f"{openai_key[:8]}...{openai_key[-4:]}" if openai_key else "미설정"
            },
            "gemini": {
                "configured": bool(gemini_key and len(gemini_key) > 5),
                "masked": f"{gemini_key[:6]}...{gemini_key[-4:]}" if gemini_key else "미설정"
            }
        }

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        if cls._cached_config is not None:
            return cls._cached_config

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 누락된 키가 있으면 기본값으로 보완
                    merged = dict(DEFAULT_CONFIG)
                    merged.update(data)
                    cls._cached_config = merged
                    return cls._cached_config
            except Exception as e:
                print(f"[AgentModelManager] 설정 파일 로드 실패, 기본값 사용: {e}")

        cls._cached_config = dict(DEFAULT_CONFIG)
        cls.save_config(cls._cached_config)
        return cls._cached_config

    @classmethod
    def save_config(cls, new_config: Dict[str, Any]) -> bool:
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            cls._cached_config = new_config
            return True
        except Exception as e:
            print(f"[AgentModelManager] 설정 저장 실패: {e}")
            return False

    @classmethod
    def get_agent_config(cls, agent_id: str) -> Dict[str, Any]:
        cfg = cls.load_config()
        return cfg.get(agent_id, DEFAULT_CONFIG.get(agent_id, {
            "model_id": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 800
        }))

    @classmethod
    def reset_to_defaults(cls) -> Dict[str, Any]:
        cls.save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    @classmethod
    def apply_preset(cls, preset_id: str) -> Dict[str, Any]:
        current = cls.load_config()
        if preset_id == "all-gpt-6-sol":
            for k in current:
                current[k]["model_id"] = "gpt-6.1-sol"
            current["calc_agent"]["reasoning_effort"] = "low"
            current["calc_agent"]["temperature"] = 0.1
            current["procedure_agent"]["reasoning_effort"] = "low"
            current["procedure_agent"]["temperature"] = 0.1
            current["infer_agent"]["reasoning_effort"] = "medium"
            current["infer_agent"]["temperature"] = 0.2
            current["public_agent"]["reasoning_effort"] = "medium"
            current["public_agent"]["temperature"] = 0.2
            current["history_agent"]["reasoning_effort"] = "high"
            current["history_agent"]["temperature"] = 0.2
            current["tactics_agent"]["reasoning_effort"] = "high"
            current["tactics_agent"]["temperature"] = 0.3
            current["coordinator_agent"]["reasoning_effort"] = "high"
            current["coordinator_agent"]["temperature"] = 0.2
            current["main_chatbot"]["reasoning_effort"] = "high"
            current["main_chatbot"]["temperature"] = 0.2
        elif preset_id == "all-gemini-38-flash":
            for k in current:
                current[k]["model_id"] = "gemini-3.8-flash"
            current["calc_agent"]["reasoning_effort"] = "low"
            current["procedure_agent"]["reasoning_effort"] = "low"
            current["infer_agent"]["reasoning_effort"] = "medium"
            current["public_agent"]["reasoning_effort"] = "medium"
            current["history_agent"]["reasoning_effort"] = "high"
            current["tactics_agent"]["reasoning_effort"] = "high"
            current["coordinator_agent"]["reasoning_effort"] = "high"
            current["main_chatbot"]["reasoning_effort"] = "high"
        elif preset_id == "all-gpt-4o-mini":
            for k in current:
                current[k]["model_id"] = "gpt-4o-mini"
            current["calc_agent"]["reasoning_effort"] = "low"
            current["procedure_agent"]["reasoning_effort"] = "low"
            current["infer_agent"]["reasoning_effort"] = "medium"
            current["public_agent"]["reasoning_effort"] = "medium"
            current["history_agent"]["reasoning_effort"] = "high"
            current["tactics_agent"]["reasoning_effort"] = "high"
            current["coordinator_agent"]["reasoning_effort"] = "high"
            current["main_chatbot"]["reasoning_effort"] = "high"
        elif preset_id == "all-gpt-4o":
            for k in current:
                current[k]["model_id"] = "gpt-4o"
            current["calc_agent"]["reasoning_effort"] = "low"
            current["procedure_agent"]["reasoning_effort"] = "low"
            current["infer_agent"]["reasoning_effort"] = "medium"
            current["public_agent"]["reasoning_effort"] = "medium"
            current["history_agent"]["reasoning_effort"] = "high"
            current["tactics_agent"]["reasoning_effort"] = "high"
            current["coordinator_agent"]["reasoning_effort"] = "high"
            current["main_chatbot"]["reasoning_effort"] = "high"
        elif preset_id == "all-gemini-flash":
            for k in current:
                current[k]["model_id"] = "gemini-3.8-flash"
        elif preset_id == "all-offline":
            for k in current:
                current[k]["model_id"] = "offline-heuristic"
        elif preset_id == "hybrid-recommended":
            current["calc_agent"]["model_id"] = "gemini-3.8-flash"
            current["calc_agent"]["reasoning_effort"] = "medium"
            current["calc_agent"]["temperature"] = 0.1
            current["calc_agent"]["max_tokens"] = 500
            current["calc_agent"]["note"] = "수량계산 & 위법판정관 [★Gemini 특화] (0.5초대 초고속 연산 & 지정수량 배수 정밀 산출)"

            current["infer_agent"]["model_id"] = "gemini-3.8-flash"
            current["infer_agent"]["reasoning_effort"] = "high"
            current["infer_agent"]["temperature"] = 0.3
            current["infer_agent"]["max_tokens"] = 650
            current["infer_agent"]["note"] = "미상물질 & 화학감별관 [★Gemini 특화] (방대한 화학 지식 & MSDS 인화점·성분 심층 역산)"

            current["procedure_agent"]["model_id"] = "gpt-4o-mini"
            current["procedure_agent"]["reasoning_effort"] = "low"
            current["procedure_agent"]["temperature"] = 0.1
            current["procedure_agent"]["max_tokens"] = 500
            current["procedure_agent"]["note"] = "단속절차 & 포렌식수사관 (GPT-4o-mini: 형사소송법 적법절차 체크 & 서식 정밀 출력)"

            current["history_agent"]["model_id"] = "gpt-6.1-sol"
            current["history_agent"]["reasoning_effort"] = "medium"
            current["history_agent"]["temperature"] = 0.2
            current["history_agent"]["max_tokens"] = 750
            current["history_agent"]["note"] = "연혁법령 & 부칙해석관 [★GPT 특화] (구 소방법 연혁 추적 & 부칙 제2조 심층 법리 분석)"

            current["public_agent"]["model_id"] = "gemini-3.8-flash"
            current["public_agent"]["reasoning_effort"] = "high"
            current["public_agent"]["temperature"] = 0.2
            current["public_agent"]["max_tokens"] = 650
            current["public_agent"]["note"] = "공공데이터 & 유권해석관 [★Gemini 특화] (100만 토큰 롱컨텍스트: 대용량 사업장 DB & 유권해석 매칭)"

            current["tactics_agent"]["model_id"] = "gpt-6.1-sol"
            current["tactics_agent"]["reasoning_effort"] = "medium"
            current["tactics_agent"]["temperature"] = 0.3
            current["tactics_agent"]["max_tokens"] = 750
            current["tactics_agent"]["note"] = "기획단속 & 변명차단관 [★GPT 특화] (3대 서류 입증, 피의자 궤변 논파 & 고난도 수사전략)"

            current["coordinator_agent"]["model_id"] = "gpt-6.1-sol"
            current["coordinator_agent"]["reasoning_effort"] = "medium"
            current["coordinator_agent"]["temperature"] = 0.2
            current["coordinator_agent"]["max_tokens"] = 800
            current["coordinator_agent"]["note"] = "합동작전 총괄 지휘본부장 [★GPT 특화] (6대 에이전트 의견 종합 및 최종 작전명령서 작성)"

            current["main_chatbot"]["model_id"] = "gpt-4o-mini"
            current["main_chatbot"]["reasoning_effort"] = "low"
            current["main_chatbot"]["temperature"] = 0.2
            current["main_chatbot"]["max_tokens"] = 750
            current["main_chatbot"]["note"] = "메인 법률상담 AI 비서 (GPT-4o-mini 기본: 상단 드롭다운으로 Gemini 3.8 Flash 원클릭 전환)"

        elif preset_id == "openai-plan-optimal":
            current["calc_agent"]["model_id"] = "gpt-4o-mini"
            current["calc_agent"]["reasoning_effort"] = "low"
            current["calc_agent"]["temperature"] = 0.1
            current["calc_agent"]["max_tokens"] = 500

            current["infer_agent"]["model_id"] = "gpt-4o-mini"
            current["infer_agent"]["reasoning_effort"] = "low"
            current["infer_agent"]["temperature"] = 0.2
            current["infer_agent"]["max_tokens"] = 600

            current["procedure_agent"]["model_id"] = "gpt-4o-mini"
            current["procedure_agent"]["reasoning_effort"] = "low"
            current["procedure_agent"]["temperature"] = 0.1
            current["procedure_agent"]["max_tokens"] = 500

            current["history_agent"]["model_id"] = "gpt-6.1-sol"
            current["history_agent"]["reasoning_effort"] = "medium"
            current["history_agent"]["temperature"] = 0.2
            current["history_agent"]["max_tokens"] = 750

            current["public_agent"]["model_id"] = "gpt-4o-mini"
            current["public_agent"]["reasoning_effort"] = "low"
            current["public_agent"]["temperature"] = 0.2
            current["public_agent"]["max_tokens"] = 600

            current["tactics_agent"]["model_id"] = "gpt-6.1-sol"
            current["tactics_agent"]["reasoning_effort"] = "medium"
            current["tactics_agent"]["temperature"] = 0.3
            current["tactics_agent"]["max_tokens"] = 750

            current["coordinator_agent"]["model_id"] = "gpt-6.1-sol"
            current["coordinator_agent"]["reasoning_effort"] = "medium"
            current["coordinator_agent"]["temperature"] = 0.2
            current["coordinator_agent"]["max_tokens"] = 800

            current["main_chatbot"]["model_id"] = "gpt-4o-mini"
            current["main_chatbot"]["reasoning_effort"] = "low"
            current["main_chatbot"]["temperature"] = 0.2
            current["main_chatbot"]["max_tokens"] = 750

        cls.save_config(current)
        return current

    @classmethod
    def get_client_for_model(cls, model_id: str) -> Optional[OpenAI]:
        """
        모델 ID에 따라 OpenAI 또는 Google Gemini(OpenAI 호환 엔드포인트) 클라이언트를 반환
        """
        if model_id.startswith("gemini-"):
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                return None
            return OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        elif model_id.startswith("gpt-") or model_id.startswith("o"):
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                return None
            return OpenAI(api_key=openai_key)
        return None

    @classmethod
    def call_agent_llm(
        cls,
        agent_id: str,
        messages: List[Dict[str, str]],
        override_max_tokens: Optional[int] = None,
        override_model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        에이전트에게 할당된 모델과 파라미터로 LLM을 호출하고 결과를 반환
        """
        cfg = cls.get_agent_config(agent_id)
        model_id = override_model_id or cfg.get("model_id", "gpt-4o-mini")
        temperature = float(cfg.get("temperature", 0.2))
        max_tokens = override_max_tokens or cfg.get("max_tokens", 800)

        # 오프라인 룰 엔진이 설정된 경우
        if model_id == "offline-heuristic":
            return {
                "success": False,
                "mode": "offline",
                "model": "offline-heuristic",
                "error": "Offline mode configured"
            }

        client = cls.get_client_for_model(model_id)
        if not client:
            return {
                "success": False,
                "mode": "offline",
                "model": model_id,
                "error": f"API key not found for {model_id}"
            }

        try:
            start_time = time.time()
            create_kwargs = {
                "model": model_id,
                "messages": messages,
            }
            # 최신 차세대 추론 모델(gpt-6, o1, o3, gpt-5 등) 파라미터 자동 호환
            if any(p in model_id.lower() for p in ["gpt-6", "o1", "o3", "gpt-5"]):
                # 추론 모델은 reasoning_tokens와 completion_tokens를 합산하므로 최소 1200 버퍼 보장
                create_kwargs["max_completion_tokens"] = max(max_tokens, 1200)
                # 추론 강도 (reasoning_effort: low, medium, high) 전달 - 토큰 절약의 핵심
                effort = cfg.get("reasoning_effort", "low")
                if effort in ["low", "medium", "high"]:
                    create_kwargs["reasoning_effort"] = effort
            else:
                create_kwargs["max_tokens"] = max_tokens
                create_kwargs["temperature"] = temperature

            res = client.chat.completions.create(**create_kwargs)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "content": res.choices[0].message.content,
                "model": model_id,
                "elapsed_ms": elapsed_ms,
                "mode": "llm"
            }
        except Exception as e:
            err_msg = str(e)
            # Google Gemini 에러(크레딧 402 소진, 429 쿼터 초과, 통신 지연 등) 발생 시, OpenAI(gpt-4o-mini)로 즉각 자동 무중단 백업
            if model_id.startswith("gemini-"):
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    try:
                        fallback_client = OpenAI(api_key=openai_key)
                        fallback_model = "gpt-4o-mini"
                        fb_res = fallback_client.chat.completions.create(
                            model=fallback_model,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=temperature
                        )
                        elapsed_ms = int((time.time() - start_time) * 1000)
                        return {
                            "success": True,
                            "content": fb_res.choices[0].message.content,
                            "model": f"Gemini 3.8 Flash (안전 백업: {fallback_model})",
                            "elapsed_ms": elapsed_ms,
                            "mode": "llm"
                        }
                    except Exception as fb_err:
                        print(f"[AgentModelManager] Fallback to OpenAI gpt-4o-mini failed: {fb_err}")
            return {
                "success": False,
                "mode": "error",
                "model": model_id,
                "error": err_msg
            }

    @classmethod
    def test_model_connection(cls, model_id: str) -> Dict[str, Any]:
        """
        특정 모델의 통신 가능 여부를 1문장 핑으로 테스트
        """
        if model_id == "offline-heuristic":
            return {
                "success": True,
                "model": model_id,
                "message": "로컬 룰 엔진 정상 (외부 통신 불필요)",
                "elapsed_ms": 0
            }

        client = cls.get_client_for_model(model_id)
        if not client:
            return {
                "success": False,
                "model": model_id,
                "message": f"'{model_id}' 모델에 필요한 API 키가 .env에 설정되어 있지 않습니다.",
                "elapsed_ms": 0
            }

        start = time.time()
        try:
            create_kwargs = {
                "model": model_id,
                "messages": [{"role": "user", "content": "위험물안전관리법 특사경 지원 시스템 핑 테스트. '정상' 2글자만 출력하세요."}],
            }
            if any(p in model_id.lower() for p in ["gpt-6", "o1", "o3", "gpt-5"]):
                create_kwargs["max_completion_tokens"] = 30
            else:
                create_kwargs["max_tokens"] = 20
                create_kwargs["temperature"] = 0.2

            res = client.chat.completions.create(**create_kwargs)
            elapsed_ms = int((time.time() - start) * 1000)
            reply = res.choices[0].message.content.strip()
            return {
                "success": True,
                "model": model_id,
                "message": f"정상 응답: {reply}",
                "elapsed_ms": elapsed_ms
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            err_msg = str(e)
            if "402" in err_msg or "credits are depleted" in err_msg:
                user_msg = "Google AI Studio 선불 크레딧 소진(402) - OpenAI 모델(gpt-4o-mini 등) 사용 권장"
            else:
                user_msg = f"통신 에러: {err_msg}"
            return {
                "success": False,
                "model": model_id,
                "message": user_msg,
                "elapsed_ms": elapsed_ms
            }
