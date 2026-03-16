from __future__ import annotations

from openai import OpenAI, APIError, APITimeoutError

from core.config import get_config


def _get_client() -> OpenAI:
    cfg = get_config()
    return OpenAI(
        base_url=f"{cfg.vllm_url}/v1",
        api_key="dummy",  # vLLM은 API key 불필요
        timeout=30.0,
    )


def generate_command(messages: list[dict]) -> str:
    """
    vLLM (OpenAI 호환 엔드포인트)에 메시지를 보내고 응답 텍스트를 반환한다.
    오류 시 RuntimeError를 발생시킨다.
    """
    cfg = get_config()
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=cfg.vllm_model,
            messages=messages,
            max_tokens=128,
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()
    except APITimeoutError as e:
        raise RuntimeError(f"vLLM 응답 타임아웃: {e}") from e
    except APIError as e:
        raise RuntimeError(f"vLLM API 오류: {e}") from e
    except Exception as e:
        raise RuntimeError(f"LLM 호출 실패: {e}") from e
