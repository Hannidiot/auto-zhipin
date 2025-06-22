import os
import json
import asyncio
from urllib.parse import urlencode, quote
from playwright.async_api import BrowserContext, Page, async_playwright, expect


base_url = "https://www.zhipin.com"
cookies_path = os.getcwd() + "/cookies.json"
salary_mapping = {
    chr(0xE031): "0",
    chr(0xE032): "1",
    chr(0xE033): "2",
    chr(0xE034): "3",
    chr(0xE035): "4",
    chr(0xE036): "5",
    chr(0xE037): "6",
    chr(0xE038): "7",
    chr(0xE039): "8",
    chr(0xE03a): "9",
}


async def load_cookies(context: BrowserContext) -> None:
    if os.path.exists(cookies_path):
        with open(cookies_path, "r") as f:
            data = json.load(f)
        await context.add_cookies(data["cookies"])


async def dump_cookies(context: BrowserContext) -> None:
    cookies = await context.cookies()
    with open(cookies_path, "w") as f:
        json.dump({"cookies": cookies}, f)


async def login(context: BrowserContext, page: Page) -> bool:
    await load_cookies(context)
    await page.goto(f"{base_url}/web/user/?ka=header-login", wait_until="networkidle")
    figure = page.locator(".nav-figure")
    for _ in range(300):
        if await figure.is_visible():
            await dump_cookies(context)
            return True
        try:
            await expect(figure).to_be_visible(timeout=1000)
        except AssertionError:
            pass
    return False


def decode_salary(salary: str) -> str:
    return "".join(salary_mapping[c] if c in salary_mapping else c for c in salary)


async def main(query: str, city: str, scroll_n: int) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context()
        page = await context.new_page()
        if not await login(context, page):
            return
        await page.goto(f"{base_url}/web/geek/jobs?{urlencode(dict(query=query, city=city), quote_via=quote)}")
        prev_h = 0
        container = page.locator(".job-list-container")
        await expect(container).to_be_visible()
        await container.hover()
        for _ in range(scroll_n):
            bbox = await container.bounding_box()
            await page.mouse.wheel(0, bbox["height"] - prev_h)
            loading = container.locator(".loading-wait")
            try:
                await expect(loading).to_be_visible()
                await expect(loading).to_be_hidden()
                if bbox["height"] > prev_h:
                    prev_h = bbox["height"]
                else:
                    break
            except AssertionError:
                break
        jobs = await container.locator(".job-name").all()
        for job in jobs:
            await job.click()
            jd = page.locator(".job-detail-box")
            favor = jd.get_by_role("link", name="收藏")
            name = jd.locator(".job-name")
            salary = jd.locator(".job-salary")
            desc = jd.locator(".desc")
            await expect(desc).to_be_visible()
            if await favor.is_visible():
                print(await name.inner_text())
                print(await job.get_attribute("href"))
                print(decode_salary(await salary.inner_text()))
                print(await desc.inner_text())


if __name__ == "__main__":
    import argparse

    cliparser = argparse.ArgumentParser(description="查询匹配的职位。")
    cliparser.add_argument("-q", "--query", help="查询关键字", type=str, default="")
    cliparser.add_argument("--city", help="BOSS直聘城市代码 (默认: 100010000)", type=str, default="100010000")
    cliparser.add_argument("-n", "--scroll_n", help="最大滚动次数 (默认: 8)", type=int, default=8)
    args, _ = cliparser.parse_known_args()

    asyncio.run(main(args.query, args.city, args.scroll_n))
