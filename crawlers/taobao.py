"""淘宝（天猫/淘宝搜索）爬虫。

说明：淘宝搜索接口（s.taobao.com 与 h5api.m.taobao.com）均要求登录态与
sign/umid 签名，未登录时返回登录跳转页或风控页。此处实现真实请求流程，
若被拦截则在 crawl_report 中记录 HTTP 状态与重定向地址，便于回溯。
"""
import re
import time

from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler, normalize_item

SEARCH_URL = "https://s.taobao.com/search"


class TaobaoCrawler(BaseCrawler):
    name = "taobao"

    def crawl(self, keyword):
        meta = {"status": "ok", "message": ""}
        items = []
        resp = self.fetch(SEARCH_URL, params={"q": keyword})

        if isinstance(resp, Exception):
            return [], {"status": "error", "message": f"请求异常: {resp}"}

        final_url = resp.url
        if "login" in final_url or resp.status_code in (302, 403):
            meta = {
                "status": "blocked",
                "message": f"命中登录/风控: HTTP {resp.status_code} -> {final_url}",
            }
            return [], meta

        html = resp.text
        soup = BeautifulSoup(html, "lxml")
        for card in soup.select("div[data-category='auctions'] .item"):
            price = card.select_one(".price strong")
            sales = card.select_one(".deal-cnt")
            title = card.select_one(".title a")
            shop = card.select_one(".shopname")
            if price is None or title is None:
                continue
            items.append(
                normalize_item(
                    self.name,
                    keyword,
                    title=title.get_text(strip=True),
                    price=_to_float(price.get_text(strip=True)),
                    sales=_sales_to_int(sales.get_text(strip=True) if sales else None),
                    shop_name=shop.get_text(strip=True) if shop else "",
                )
            )
        if not items:
            meta["status"] = "empty"
            meta["message"] = "页面可访问但未解析到商品（可能为动态渲染/风控验证页）"
        return items, meta


def _to_float(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None


def _sales_to_int(text):
    text = (text or "").replace("人付款", "").replace("+", "")
    if "万" in text:
        m = re.search(r"([\d.]+)", text)
        return int(float(m.group(1)) * 10000) if m else None
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None
