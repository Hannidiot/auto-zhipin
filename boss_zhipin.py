import json
import random
from pathlib import Path
from urllib.parse import urlencode, quote
from typing import AsyncGenerator
from playwright.async_api import BrowserContext, Page, Locator, async_playwright, expect
from pydantic import BaseModel


base_url = "https://www.zhipin.com"
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


async def load_cookies(context: BrowserContext, cookies_path: Path) -> None:
    if cookies_path.exists():
        with open(cookies_path, "r") as f:
            data = json.load(f)
        await context.add_cookies(data["cookies"])


async def dump_cookies(context: BrowserContext, cookies_path: Path) -> None:
    cookies = await context.cookies()
    with open(cookies_path, "w") as f:
        json.dump({"cookies": cookies}, f)


async def login(context: BrowserContext, page: Page, cookies_path: Path) -> bool:
    await load_cookies(context, cookies_path)
    await page.goto(f"{base_url}/web/user/?ka=header-login", wait_until="networkidle")
    figure = page.locator(".nav-figure")
    for _ in range(300):
        if await figure.is_visible():
            await dump_cookies(context, cookies_path)
            return True
        try:
            await expect(figure).to_be_visible(timeout=1000)
        except AssertionError:
            pass
    return False


def decode_salary(salary: str) -> str:
    return "".join(salary_mapping[c] if c in salary_mapping else c for c in salary)


class Job:
    class Info(BaseModel):
        name: str
        salary: str
        desc: str
        url: str

    _info: Info
    _jd: Locator
    _favor: Locator

    def __init__(self, info: Info, jd: Locator, favor: Locator):
        self._info = info
        self._jd = jd
        self._favor = favor

    def description(self) -> str:
        return f"<name>{self._info.name}</name>\n<salary>{self._info.salary}</salary>\n<description>\n{self._info.desc}\n</description>"

    def model_dump(self) -> dict[str, str]:
        return self._info.model_dump()

    async def favor(self) -> None:
        await self._favor.click(delay=random.randint(32, 512))
        await expect(self._jd.get_by_role("link", name="取消收藏")).to_be_visible()


class BossZhipin:
    _cookies_path: Path

    def __init__(self, cookies_path: str = "cookies.json"):
        self._cookies_path = Path(cookies_path).resolve()

    async def query_jobs(self, query: str, city: str, scroll_n: int) -> AsyncGenerator[Job, None]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context()
            page = await context.new_page()
            if not await login(context, page, self._cookies_path):
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
                await job.click(delay=random.randint(32, 512))
                jd = page.locator(".job-detail-box")
                favor = jd.get_by_role("link", name="收藏")
                name = jd.locator(".job-name")
                salary = jd.locator(".job-salary")
                desc = jd.locator(".desc")
                await expect(desc).to_be_visible()
                if await favor.is_visible():
                    yield Job(Job.Info(
                        name = await name.inner_text(),
                        salary = decode_salary(await salary.inner_text()),
                        desc = await desc.inner_text(),
                        url = await job.get_attribute("href"),
                    ), jd, favor)
