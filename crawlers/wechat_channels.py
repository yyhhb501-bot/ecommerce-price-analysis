"""微信视频号（视频号小店）爬虫。

说明：视频号小店搜索接口（channels.weixin.qq.com）依赖微信登录态与
X-WECHAT-KEY 等签名，无登录时返回空壳/风控页。此处实现真实请求流程并记录状态。
视频号用户以中老年为主，客单价与品质要求相对更高，是本项目重点平台。
"""
import re

from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler, normalize_item

SEARCH_URL = "https://channels.weixin.qq.com/shop/search"


class WechatChannelsCrawler(BaseCrawler):
    name = "wechat_channels"

    def crawl(self, keyword):
        meta = {"status": "ok", "message": ""}
        items = []
        resp = self.fetch(SEARCH_URL, params={"keyword": keyword})

        if isinstance(resp, Exception):
            return [], {"status": "error", "message": f"请求异常: {resp}"}

        if "login" in resp.url or "auth" in resp.url or resp.status_code in (302, 403):
            meta = {
                "status": "blocked",
                "message": f"命中登录/风控: HTTP {resp.status_code} -> {resp.url}",
            }
            return [], meta

        soup = BeautifulSoup(resp.text, "lxml")
        for card in soup.select("[class*='goods'], [class*='product']"):
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
            meta["message"] = "页面为 JS 渲染空壳，未取到商品（需登录态）"
        return items, meta


def _to_float(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return float(m.group()) if m else None
