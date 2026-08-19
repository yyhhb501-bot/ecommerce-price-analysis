"""抖音商城爬虫。

说明：抖音商城搜索（haohuo.jinritemai.com）与 douyin.com 搜索均需 X-Bogus /
a_bogus 签名及登录态，无签名时返回空壳页或风控。此处实现真实请求流程并记录状态。
"""
import re

from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler, normalize_item

SEARCH_URL = "https://haohuo.jinritemai.com/views/search/index"


class DouyinCrawler(BaseCrawler):
    name = "douyin"

    def crawl(self, keyword):
        meta = {"status": "ok", "message": ""}
        items = []
        resp = self.fetch(SEARCH_URL, params={"keyword": keyword})

        if isinstance(resp, Exception):
            return [], {"status": "error", "message": f"请求异常: {resp}"}

        if "login" in resp.url or resp.status_code in (302, 403):
            meta = {
                "status": "blocked",
                "message": f"命中风控/登录: HTTP {resp.status_code} -> {resp.url}",
            }
            return [], meta

        soup = BeautifulSoup(resp.text, "lxml")
        for card in soup.select(".product-card, [class*='product']"):
            title = card.select_one("[class*='title'], [class*='name']")
            price = card.select_one("[class*='price']")
            if not title or not price:
                continue
            items.append(
                normalize_item(
                    self.name,
                    keyword,
                    title=title.get_text(strip=True),
                    price=_to_float(price.get_text(strip=True)),
                )
            )
        if not items:
            meta["status"] = "empty"
            meta["message"] = "页面为 JS 渲染空壳，未取到商品（需签名）"
        return items, meta


def _to_float(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None
