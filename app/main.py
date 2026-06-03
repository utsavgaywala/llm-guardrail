"""
LLM GuardRail — Main API
========================
Every chat request flows through:
  Step 1: Input Guardrails  (block bad input)
  Step 2: LLM Call          (get AI response)
  Step 3: Output Guardrails (validate response)
  Step 4: Logger            (save to database)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.guardrails.input_guard import InputGuardrail
from app.guardrails.output_guard import OutputGuardrail
from app.guardrails.policy_engine import PolicyEngine
from app.api.llm_client import LLMClient
from app.logger import RequestLogger
import time

app = FastAPI(
    title="LLM GuardRail",
    description="Production-grade safety middleware for LLM applications",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

policy_engine = PolicyEngine(config_path="config/policies.yaml")
input_guard   = InputGuardrail(policy_engine)
output_guard  = OutputGuardrail(policy_engine)
llm_client    = LLMClient()
logger        = RequestLogger()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"


class ChatResponse(BaseModel):
    response: str
    blocked: bool
    block_reason: str | None
    checks_performed: list[str]
    latency_ms: float


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    all_checks = []

    # Step 1: Input Guardrails
    input_result = await input_guard.check(request.message)
    all_checks.extend(input_result["checks"])

    if input_result["blocked"]:
        latency = round((time.time() - start_time) * 1000, 2)
        logger.log(
            user_id=request.user_id,
            message=request.message,
            blocked=True,
            block_reason=input_result["reason"],
            latency_ms=latency,
            checks=all_checks
        )
        return ChatResponse(
            response="Sorry, I cannot process that request. Please rephrase and try again.",
            blocked=True,
            block_reason=input_result["reason"],
            checks_performed=all_checks,
            latency_ms=latency
        )

    # Step 2: Call LLM
    try:
        system_prompt = policy_engine.get_system_prompt()
        llm_response  = await llm_client.complete(
            user_message=request.message,
            system_prompt=system_prompt
        )
        all_checks.append("llm_call: success")
    except RuntimeError as e:
        latency = round((time.time() - start_time) * 1000, 2)
        logger.log(
            user_id=request.user_id,
            message=request.message,
            blocked=True,
            block_reason=str(e),
            latency_ms=latency,
            checks=all_checks + ["llm_call: FAILED"]
        )
        return ChatResponse(
            response="LLM service is currently unavailable. Please try again later.",
            blocked=True,
            block_reason=str(e),
            checks_performed=all_checks + ["llm_call: FAILED"],
            latency_ms=latency
        )

    # Step 3: Output Guardrails
    output_result = await output_guard.check(llm_response)
    all_checks.extend(output_result["checks"])

    if output_result["blocked"]:
        print("[GuardRail] Output blocked, auto-retrying...")
        try:
            retry_response = await llm_client.complete(
                user_message=request.message,
                system_prompt=system_prompt + "\nIMPORTANT: Keep your response safe, helpful and concise."
            )
            retry_result = await output_guard.check(retry_response)

            if retry_result["blocked"]:
                latency = round((time.time() - start_time) * 1000, 2)
                logger.log(
                    user_id=request.user_id,
                    message=request.message,
                    blocked=True,
                    block_reason=output_result["reason"],
                    latency_ms=latency,
                    checks=all_checks + ["auto_retry: also_blocked"]
                )
                return ChatResponse(
                    response="I was unable to generate a safe response. Please try rephrasing.",
                    blocked=True,
                    block_reason=output_result["reason"],
                    checks_performed=all_checks + ["auto_retry: also_blocked"],
                    latency_ms=latency
                )

            llm_response = retry_response
            all_checks.append("auto_retry: success")

        except RuntimeError as e:
            latency = round((time.time() - start_time) * 1000, 2)
            logger.log(
                user_id=request.user_id,
                message=request.message,
                blocked=True,
                block_reason=str(e),
                latency_ms=latency,
                checks=all_checks + ["auto_retry: FAILED"]
            )
            return ChatResponse(
                response="LLM service is currently unavailable. Please try again later.",
                blocked=True,
                block_reason=str(e),
                checks_performed=all_checks + ["auto_retry: FAILED"],
                latency_ms=latency
            )

    # Step 4: Log the request
    latency = round((time.time() - start_time) * 1000, 2)
    logger.log(
        user_id=request.user_id,
        message=request.message,
        blocked=False,
        block_reason=None,
        latency_ms=latency,
        checks=all_checks
    )

    return ChatResponse(
        response=llm_response,
        blocked=False,
        block_reason=None,
        checks_performed=all_checks,
        latency_ms=latency
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "policies_loaded": len(policy_engine.policies)
    }


@app.get("/policies")
def list_policies():
    return {"policies": policy_engine.policies}


@app.get("/stats")
def get_stats():
    return logger.get_stats()


@app.get("/logs")
def get_logs():
    logs = logger.get_all_logs()
    return {"logs": [
        {
            "timestamp":    row[0],
            "user_id":      row[1],
            "message":      row[2][:50],
            "blocked":      bool(row[3]),
            "block_reason": row[4],
            "latency_ms":   row[5]
        }
        for row in logs
    ]}