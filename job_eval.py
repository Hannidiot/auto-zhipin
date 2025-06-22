import re
import json
import asyncio
from datetime import date
from pydantic import BaseModel
from typing import Callable, Awaitable
from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.request_params import RequestParams


def remove_json_fences(raw: str):
    return re.sub(r"`{3}(json)?\n?", "", raw)


class Evaluator(BaseModel):
    name: str = "eval"
    instruction: str = f"""你是一位非常专业的职业导师，请根据以下标准评判工作岗位与求职者的匹配程度:

1. 教育背景: 求职者的学历与岗位要求是否一致？与岗位相关的专业背景或学位是否符合？
2. 工作经验: 求职者的工作经历是否与岗位要求的工作年限、工作领域相关？求职者是否有类似行业或领域的工作经验？
3. 技能要求: 简历中列出的技能是否符合岗位要求的技术栈、工具、语言等？求职者是否具备额外的技能，可能对岗位有所加分？
4. 成就与业绩: 求职者是否在简历中列出了与岗位相关的成果或项目经验？求职者是否有量化的业绩数据来支持其能力？
5. 文化适配: 求职者是否在简历中表现出与公司文化或团队环境相符的特点？求职者是否有跨文化沟通或适应不同工作环境的经验？

请针对每项标准提供评级 (EXCELLENT, GOOD, FAIR, or POOR)。"""

    @staticmethod
    def request_params() -> RequestParams:
        return RequestParams(maxTokens=8192, temperature=0.4)

    @staticmethod
    def prompt(resume: str, job_description: str) -> str:
        today = str(date.today())
        return f"""<bio-resume>
{resume}
</bio-resume>

<job-description>
{job_description}
</job-description>

今天是{today}，请评判该岗位与求职者的匹配程度。"""


class EvalSummary(BaseModel):
    name: str = "eval_summary"
    instruction: str = """Summarize the evaluation as a structured response with the overall match rating.

Your response MUST be valid JSON matching this exact format (no other text, markdown, or explanation):

{"rating":"RATING"}

Where:

- RATING: Must be one of: "EXCELLENT", "GOOD", "FAIR", or "POOR"
- EXCELLENT: Perfect match
- GOOD: General match
- FAIR: General mismatch
- POOR: Complete mismatch

IMPORTANT: Your response should be ONLY the JSON object without any code fences, explanations, or other text."""
    use_history: bool = False

    @staticmethod
    def request_params() -> RequestParams:
        return RequestParams(
            maxTokens = 8192,
            temperature = 0.4,
            use_history = False
        )


if __name__ == "__main__":
    import sys
    import argparse

    cliparser = argparse.ArgumentParser(description="Start to evaluate a job description.")
    cliparser.add_argument("--resume", help="Path of the candidate resume file (default: resume.md)", type=str, default="resume.md")
    args, _ = cliparser.parse_known_args()

    with open(args.resume, "r") as f:
        resume = f.read()
    job_description = sys.stdin.read()

    # Create the application
    fast = FastAgent("job-eval", parse_cli_args=False)
    # Define generator agent
    @fast.agent(**Evaluator().model_dump(), request_params=Evaluator.request_params())
    @fast.agent(**EvalSummary().model_dump(), request_params=EvalSummary.request_params())
    async def main() -> None:
        async with fast.run() as agent:
            evaluation = await agent.eval(Evaluator.prompt(resume, job_description))
            await agent.eval_summary(evaluation)

    asyncio.run(main())
