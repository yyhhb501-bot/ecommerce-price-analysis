"""爬虫调度：对每个「品类 × 平台」执行一次真实抓取尝试，汇总为 crawl_report.json。"""
import json
import os
from datetime import datetime

from crawlers.douyin import DouyinCrawler
from crawlers.pinduoduo import PinduoduoCrawler
from crawlers.taobao import TaobaoCrawler
from config import CATEGORIES, RAW_DIR

CRAWLERS = {
    "taobao": TaobaoCrawler,
    "pinduoduo": PinduoduoCrawler,
    "douyin": DouyinCrawler,
}


def run_all():
    os.makedirs(RAW_DIR, exist_ok=True)
    summary = []
    for category in CATEGORIES:
        for name, cls in CRAWLERS.items():
            crawler = cls()
            print(f"[crawl] {name} / {category} ...")
            items, meta = crawler.crawl(category)
            fname = crawler.save_report(category, items, meta)
            summary.append(
                {
                    "platform": name,
                    "category": category,
                    "status": meta.get("status"),
                    "message": meta.get("message", ""),
                    "items": len(items),
                    "file": fname,
                }
            )
            print(f"  -> {meta.get('status')}: {len(items)} 条  ({meta.get('message','')})")

    out = {
        "crawl_time": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
    }
    with open(os.path.join(RAW_DIR, "crawl_report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n抓取汇总已写入 data/raw/crawl_report.json")
    return out


if __name__ == "__main__":
    run_all()
