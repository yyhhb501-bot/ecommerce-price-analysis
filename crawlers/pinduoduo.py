"""拼多多爬虫。

说明：拼多多 H5 搜索（mobile.yangkeduo.com）依赖 anti-content 加密参数与
登录 Cookie，无签名时返回风控页/验证码。此处实现真实请求流程并记录拦截状态。
"""
import re

from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler, normalize_item

SEARCH_URL = "https://mobile.yangkeduo.com/search_result.html"


class PinduoduoCrawler(BaseCrawler):
    name = "pinduoduo"

    def crawl(self, keyword):
        meta = {"status": "ok", "message": ""}
        items = []
        resp = self.fetch(SEARCH_URL, params={"search_key": keyword})

        if isinstance(resp, Exception):
            return [], {"status": "error", "message": f"请求异常: {resp}"}

        if "verify" in resp.url or "login" in resp.url or resp.status_code in (302, 403):
            meta = {
                "status": "blocked",
                "message": f"命中风控/登录: HTTP {resp.status_code} -> {resp.url}",
            }
            return [], meta

        soup = BeautifulSoup(resp.text, "lxml")
        for card in soup.select("._1Z9iMBYZnA ._3GwDb1bLkM, .good-item"):
            title = card.select_one(".goods-name, .p-name")
            price = card.select_one(".goods-price, .p-price")
            sales = card.select_one(".goods-sales, .p-sales")
            if not title or not price:
                continue
            items.append(
                normalize_item(
                    self.name,
                    keyword,
                    title=title.get_text(strip=True),
                    price=_to_float(price.get_text(strip=True)),
                    sales=_sales_to_int(sales.get_text(strip=True) if sales else None),
                )
            )
        if not items:
            meta["status"] = "empty"
            meta["message"] = "页面可访问但未解析到商品（可能为验证码页）"
        return items, meta


def _to_float(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None


def _sales_to_int(text):
    text = (text or "").replace("已拼", "").replace("件", "").replace("+", "")
    if "万" in text:
        m = re.search(r"([\d.]+)", text)
        return int(float(m.group(1)) * 10000) if m else None
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None
