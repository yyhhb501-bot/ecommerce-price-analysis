"""备用参考数据生成器。

当真实抓取被平台风控拦截时，用贴近真实市场分布的参考数据补齐，保证分析可跑通。
所有生成记录 data_source='reference'（估测），与真实抓取 'crawled' 严格区分，
报告中会明确标注。

分布依据：公开渠道可查的常见价格带与销量量级（白牌/低价走量 vs 品牌中高价）。
"""
import csv
import math
import os
import random
from datetime import datetime

from config import RAW_DIR, MIN_SKUS_PER_GROUP, FALLBACK_SEED

# 每个「平台 × 品类」的价格分布（单位：元）
PRICE_SPECS = {
    "polo衫": {
        "淘宝": {"center": 79, "std": 25, "lo": 39, "hi": 199},
        "拼多多": {"center": 39, "std": 12, "lo": 19, "hi": 89},
        "抖音": {"center": 69, "std": 22, "lo": 39, "hi": 159},
        "微信视频号": {"center": 99, "std": 30, "lo": 49, "hi": 199},
    },
    "牛仔裤": {
        "淘宝": {"center": 129, "std": 40, "lo": 59, "hi": 299},
        "拼多多": {"center": 49, "std": 15, "lo": 29, "hi": 129},
        "抖音": {"center": 89, "std": 30, "lo": 49, "hi": 199},
        "微信视频号": {"center": 119, "std": 35, "lo": 59, "hi": 229},
    },
}

# 销量量级基数（件，近 30 天口径）
SALES_BASE = {
    "淘宝": 800,
    "拼多多": 12000,
    "抖音": 3000,
    "微信视频号": 2500,
}

TITLE_TEMPLATES = {
    "polo衫": [
        "{brand} 冰丝polo衫 男 夏季 翻领短袖 商务休闲",
        "{brand} 纯棉polo衫 女 宽松显瘦 短袖上衣",
        "{brand} 重磅珠地棉polo衫 免烫 通勤百搭",
        "{brand} 针织polo衫 薄款 透气 中青年",
        "{brand} 情侣款polo衫 半袖 潮流 纯色",
        "{brand} 中老年polo衫 爸爸装 冰丝短袖 舒适透气",
    ],
    "牛仔裤": [
        "{brand} 牛仔裤 男 直筒 宽松 大码 百搭",
        "{brand} 牛仔裤 女 高腰 小脚 显瘦 弹力",
        "{brand} 锥形牛仔裤 九分 春夏薄款",
        "{brand} 阔腿牛仔裤 复古 水洗 做旧",
        "{brand} 加绒牛仔裤 秋冬 保暖 直筒",
        "{brand} 中老年牛仔裤 宽松直筒 高腰 舒适",
    ],
}

BRANDS = ["白牌", "无品牌", "自主品牌", "工厂直供"]


def _gen_price(rng, spec):
    v = rng.gauss(spec["center"], spec["std"])
    return round(min(max(v, spec["lo"]), spec["hi"]))


def _gen_sales(rng, price, platform, spec):
    # 价格相对平台价格带越高、销量越低（负相关），叠加对数正态噪声
    lo, hi = spec["lo"], spec["hi"]
    norm = (price - lo) / max(hi - lo, 1.0)
    mu = math.log(SALES_BASE[platform]) - norm * 3.0
    sales = int(round(rng.lognormvariate(mu, 0.55)))
    return max(sales, 1)


def _gen_title(rng, category):
    tpl = rng.choice(TITLE_TEMPLATES[category])
    brand = rng.choice(BRANDS)
    return tpl.format(brand=brand)


def generate():
    rng = random.Random(FALLBACK_SEED)
    rows = []
    now = datetime.now().isoformat(timespec="seconds")
    sid = 0

    for category, platform_specs in PRICE_SPECS.items():
        for platform, spec in platform_specs.items():
            for _ in range(MIN_SKUS_PER_GROUP):
                price = _gen_price(rng, spec)
                sales = _gen_sales(rng, price, platform, spec)
                comments = int(round(sales * rng.uniform(0.2, 0.6)))
                original = round(price * rng.uniform(1.25, 1.55))
                sid += 1
                rows.append(
                    {
                        "sku_id": f"REF{sid:04d}",
                        "platform": platform,
                        "category": category,
                        "title": _gen_title(rng, category),
                        "brand": "白牌" if rng.random() < 0.75 else rng.choice(BRANDS),
                        "price": price,
                        "original_price": original,
                        "sales": sales,
                        "sales_unit": "近30天",
                        "comments": comments,
                        "shop_name": f"{platform}示范店铺{rng.randint(1, 99)}",
                        "data_source": "reference",
                        "crawl_time": now,
                    }
                )

    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, "reference_data.csv")
    fields = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"备用参考数据已生成: {out_path} ({len(rows)} 条)")
    return out_path


if __name__ == "__main__":
    generate()
