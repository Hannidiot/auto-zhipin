import json
import asyncio
import argparse
from boss_zhipin import BossZhipin
from job_eval import spawn_workflow


if __name__ == "__main__":
    cliparser = argparse.ArgumentParser(description="查询匹配的职位。")
    cliparser.add_argument("--resume", help="简历文件路径 (目前只支持文本文件，推荐使用Markdown)", type=str, required=True)
    cliparser.add_argument("-q", "--query", help="查询关键字", type=str, default="")
    cliparser.add_argument("--city", help="BOSS直聘城市代码 (默认: 100010000)", type=str, default="100010000")
    cliparser.add_argument("-n", "--scroll_n", help="最大滚动次数 (默认: 8)", type=int, default=8)
    cliparser.add_argument("--ratings", help="可接受的岗位评级 (默认: EXCELLENT,GOOD)", type=str, default="EXCELLENT,GOOD")
    cliparser.add_argument("-O", "--output", help="输出文件路径 (默认: favor_jobs.json)", type=str, default="favor_jobs.json")
    args, _ = cliparser.parse_known_args()

    async def main() -> None:
        ratings = set(r.strip() for r in args.ratings.split(","))
        with open(args.resume, "r") as f:
            resume = f.read()
        favor_jobs = []
        zhipin = BossZhipin()
        async for job in zhipin.query_jobs(args.query, args.city, args.scroll_n):
            workflow = spawn_workflow()
            result = json.loads(await workflow(resume, job.description()))
            if result["rating"] in ratings:
                await job.favor()
                favor_jobs.append(job.model_dump())
        if len(favor_jobs) > 0:
            with open(args.output, "w") as f:
                json.dump(favor_jobs, f)

    asyncio.run(main())
