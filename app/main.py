import json
import time
import os
from typing import Dict, Any
from datetime import datetime

import boto3
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datadog import DogStatsdClient
from ddtrace import tracer


logger = structlog.get_logger()


class GenerateRequest(BaseModel):
    prompt: str
    user_id: str
    max_tokens: int = 1000


class GenerateResponse(BaseModel):
    response: str
    tokens_used: int
    latency_ms: float
    cost_usd: float


app = FastAPI(
    title="GenAI Guardian - Bedrock Proxy",
    description="FastAPI proxy for Amazon Bedrock with Datadog monitoring",
    version="1.0.0"
)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
)

statsd = DogStatsdClient(
    host=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_DOGSTATSD_PORT", "8125"))
)

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
SERVICE_NAME = os.getenv("DD_SERVICE", "my-bedrock-proxy")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": SERVICE_NAME}


@app.post("/generate", response_model=GenerateResponse)
@tracer.wrap("bedrock.generate")
async def generate_text(request: GenerateRequest):
    start_time = time.time()
    
    try:
        logger.info(
            "generate_request_received",
            user_id=request.user_id,
            prompt_length=len(request.prompt),
            model=BEDROCK_MODEL_ID
        )
        
        # Prepare Bedrock request
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        }
        
        # Call Bedrock
        with tracer.trace("bedrock.invoke_model") as span:
            span.set_tag("model", BEDROCK_MODEL_ID)
            span.set_tag("user_id", request.user_id)
            
            response = bedrock.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType="application/json"
            )
        
        # Parse response
        response_body = json.loads(response["body"].read())
        generated_text = response_body["content"][0]["text"]
        
        # Calculate metrics
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Estimate tokens and cost (Claude Sonnet pricing)
        input_tokens = len(request.prompt.split()) * 1.3  # Rough estimation
        output_tokens = len(generated_text.split()) * 1.3
        total_tokens = int(input_tokens + output_tokens)
        
        # Claude 3.5 Sonnet pricing (per 1M tokens)
        input_cost_per_token = 0.003 / 1_000_000
        output_cost_per_token = 0.015 / 1_000_000
        cost_usd = (input_tokens * input_cost_per_token) + (output_tokens * output_cost_per_token)
        
        # Emit metrics to Datadog
        statsd.increment(
            "bedrock.requests.total",
            tags=[
                f"model:{BEDROCK_MODEL_ID}",
                f"service:{SERVICE_NAME}",
                f"user_id:{request.user_id}"
            ]
        )
        
        statsd.histogram(
            "bedrock.latency_ms",
            latency_ms,
            tags=[
                f"model:{BEDROCK_MODEL_ID}",
                f"service:{SERVICE_NAME}"
            ]
        )
        
        statsd.histogram(
            "bedrock.tokens_used",
            total_tokens,
            tags=[
                f"model:{BEDROCK_MODEL_ID}",
                f"service:{SERVICE_NAME}",
                "type:total"
            ]
        )
        
        statsd.histogram(
            "bedrock.cost_usd",
            cost_usd,
            tags=[
                f"model:{BEDROCK_MODEL_ID}",
                f"service:{SERVICE_NAME}"
            ]
        )
        
        logger.info(
            "generate_request_completed",
            user_id=request.user_id,
            latency_ms=latency_ms,
            tokens_used=total_tokens,
            cost_usd=cost_usd,
            model=BEDROCK_MODEL_ID
        )
        
        return GenerateResponse(
            response=generated_text,
            tokens_used=total_tokens,
            latency_ms=latency_ms,
            cost_usd=round(cost_usd, 6)
        )
        
    except Exception as e:
        # Emit error metric
        statsd.increment(
            "bedrock.requests.errors",
            tags=[
                f"model:{BEDROCK_MODEL_ID}",
                f"service:{SERVICE_NAME}",
                f"error_type:{type(e).__name__}"
            ]
        )
        
        logger.error(
            "generate_request_failed",
            user_id=request.user_id,
            error=str(e),
            model=BEDROCK_MODEL_ID
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate text: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)