"""爬虫公共基类：请求、限流、重试与结果记录。"""
import json
import os
import random
import time

import requests

from config import RAW_DIR, REQUEST_TIMEOUT, RETRY_TIMES, REQUEST_INTERVAL

# 真实浏览器 User-Agent 池
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]


class BaseCrawler:
    name = "base"

    def __init__(self):
        self.session = requests.Session()

    def _headers(self):
        return {
            "User-Agent": random.choice(UA_POOL),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

    def fetch(self, url, params=None, **kwargs):
        """带重试与限流的 GET 请求，返回 Response 或 None。"""
        last_err = None
        for attempt in range(RETRY_TIMES + 1):
            try:
                resp = self.session.get(
                    url,
                    params=params,
                    headers=self._headers(),
                    timeout=REQUEST_TIMEOUT,
                    **kwargs,
                )
                time.sleep(REQUEST_INTERVAL)
                return resp
            except requests.RequestException as exc:  # pragma: no cover
                last_err = exc
                time.sleep(REQUEST_INTERVAL * (attempt + 1))
        return last_err

    def crawl(self, keyword):
        """子类实现：返回 (items, meta)。items 为标准 SKU dict 列表。"""
        raise NotImplementedError

    def save_report(self, keyword, items, meta):
        os.makedirs(RAW_DIR, exist_ok=True)
        report = {
            "platform": self.name,
            "keyword": keyword,
            "status": meta.get("status", "ok"),
            "message": meta.get("message", ""),
            "items_count": len(items),
            "items": items,
        }
        fname = f"{self.name}_{keyword}.json"
        with open(os.path.join(RAW_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return fname


def normalize_item(platform, category, **fields):
    """统一 SKU 口径。"""
    return {
        "platform": platform,
        "category": category,
        "title": fields.get("title", ""),
        "brand": fields.get("brand", ""),
        "price": fields.get("price"),
        "original_price": fields.get("original_price"),
        "sales": fields.get("sales"),
        "sales_unit": fields.get("sales_unit", ""),
        "comments": fields.get("comments"),
        "shop_name": fields.get("shop_name", ""),
        "data_source": fields.get("data_source", "crawled"),
        "crawl_time": fields.get("crawl_time", ""),
    }
