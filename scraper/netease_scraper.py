"""
新浪新闻爬虫 - 从 feed.mix.sina.com.cn 滚动接口爬取新闻列表
================================================================
数据源: 新浪新闻公开 API（无需认证，直接 JSON 响应）
输出格式: JSON 数组，兼容管理端 ImportNewsItem 格式

核心功能:
  - 多频道爬取（财经、科技、体育、娱乐、国际）
  - 深度抓取（逐篇抓取详情页正文和封面图，保留段落结构）
  - 编码修正（新浪服务器不返回 charset，需手动指定 UTF-8）
  - 去重（同 URL 自动跳过）
  - 分类映射（新浪频道 → 数据库分类 ID）

用法:
  python scraper/netease_scraper.py                  # CLI: 输出 40 条到终端
  python scraper/netease_scraper.py -n 20 -o out.json # CLI: 爬 20 条输出到文件
  fetch_sina_news(count, lids, deep=True)             # 模块调用: 供后端 API 使用
"""

import json
import re
import argparse
import requests
from datetime import datetime

# 新浪新闻滚动 API（公开接口，无需认证）
SINA_API = "https://feed.mix.sina.com.cn/api/roll/get"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://news.sina.com.cn/",
}

# 分类映射: 新浪频道 lid → 数据库分类 ID
# 你的数据库: 1=头条 2=社会 3=国内 4=国际 5=娱乐 6=体育 7=科技 8=财经
CATEGORY_MAP = {
    2509: 8,   # 财经
    2510: 7,   # 科技
    2511: 6,   # 体育
    2669: 5,   # 娱乐
    2514: 4,   # 国际
    2515: 8,   # 商业 → 财经
    2513: 5,   # 电影 → 娱乐
    2968: 6,   # 体育
    2970: 7,   # 科技
}
DEFAULT_CATEGORY = 1  # 未匹配的默认放头条

# 所有频道均需 pageid=153
PAGE_ID = 153


def fetch_article_content(url: str, timeout: int = 10) -> tuple[str, str]:
    """
    深度抓取一篇新浪新闻的详情页
    步骤: 请求文章URL → 修正编码 → 提取正文区域 → 分离段落和图片 → 过滤尾部干扰
    返回: (正文内容, 封面图URL)，失败返回 ("", "")
    正文格式: 段落间用双换行分隔，已过滤责任编辑等尾部信息
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text

        # 提取正文区域
        article_html = ""
        for pattern in [
            r'class="article"[^>]*>(.*?)</div>',
            r'id="artibody"[^>]*>(.*?)</div>',
            r'class="article-content"[^>]*>(.*?)</div>',
            r'<article[^>]*>(.*?)</article>',
        ]:
            m = re.search(pattern, html, re.DOTALL)
            if m:
                article_html = m.group(1)
                break

        if not article_html:
            return "", ""

        # 提取图片
        image_url = ""
        img_match = re.search(r'<img[^>]*src="([^"]+)"', article_html, re.I)
        if img_match:
            img = img_match.group(1)
            if img.startswith("//"):
                img = "https:" + img
            elif img.startswith("http"):
                pass
            else:
                img = ""
            image_url = img

        # 提取所有 <p> 段落
        paragraphs = []
        junk_keywords = ["责任编辑", "举报", "投诉", "相关阅读", "推荐阅读", "特别声明"]

        for p_tag in re.findall(r'<p[^>]*>(.*?)</p>', article_html, re.DOTALL):
            text = re.sub(r'<[^>]+>', '', p_tag).strip()
            if len(text) < 10:
                continue
            is_junk = any(kw in text for kw in junk_keywords)
            if is_junk:
                continue
            paragraphs.append(text)

        if paragraphs:
            content = "\n\n".join(paragraphs)
            return content, image_url
    except Exception:
        pass
    return "", ""


def fetch_sina_news(count: int = 40, lids: list[int] | None = None, deep: bool = False):
    """
    从新浪新闻 API 爬取新闻列表
    参数:
      count: 目标爬取数量
      lids: 频道 ID 列表（新浪内部编号），None 默认财经频道
      deep: 是否深度抓取（True=逐篇抓详情页正文+封面图，False=仅列表摘要）
    返回: 新闻字典列表，字段与 ImportNewsItem schema 对齐
    去重: 基于 sourceUrl 自动跳过已爬取的 URL
    """
    if lids is None:
        lids = [2509]  # 默认财经频道

    all_items = []
    seen_urls = set()
    num = 20

    # 每个频道分配配额
    per_channel = max(count // len(lids), 20)

    for lid in lids:
        page = 1
        channel_count = 0

        while channel_count < per_channel and len(all_items) < count:
            params = {
                "pageid": PAGE_ID,
                "lid": lid,
                "k": "",
                "num": num,
                "page": page,
            }
            resp = requests.get(SINA_API, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("result", {}).get("data", [])
            if not items:
                break

            for item in items:
                title = item.get("title", "").strip()
                url = item.get("url", "").strip()
                intro = item.get("intro", "").strip()
                ctime = item.get("ctime", "")
                media_name = item.get("media_name", "").strip()
                keywords = item.get("keywords", "").strip()

                if not title:
                    continue

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                try:
                    ts = int(ctime)
                    dt = datetime.fromtimestamp(ts)
                    publish_time = dt.strftime("%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError):
                    publish_time = ctime

                all_items.append({
                    "title": title,
                    "description": intro,
                    "content": "",
                    "author": media_name,
                    "sourceUrl": url,
                    "image": "",
                    "publishTime": publish_time,
                    "categoryId": CATEGORY_MAP.get(lid, DEFAULT_CATEGORY),
                    "keywords": keywords,
                    "_deep": deep,
                })
                channel_count += 1

                if len(all_items) >= count:
                    break

            page += 1
            if page > 5:
                break

    # 深度抓取正文 + 封面图
    if deep and all_items:
        print(f"  正在抓取 {len(all_items)} 篇文章正文...", flush=True)
        for i, item in enumerate(all_items):
            if item.get("sourceUrl"):
                content, image = fetch_article_content(item["sourceUrl"])
                if content:
                    item["content"] = content
                if image and not item.get("image"):
                    item["image"] = image
            if (i + 1) % 10 == 0:
                print(f"    {i+1}/{len(all_items)}...", flush=True)

    return all_items[:count]


def main():
    parser = argparse.ArgumentParser(description="新浪新闻爬虫")
    parser.add_argument("-o", "--output", help="输出 JSON 文件路径")
    parser.add_argument("-n", "--count", type=int, default=40, help="爬取数量 (默认40)")
    parser.add_argument("-p", "--pretty", action="store_true", help="格式化输出")
    parser.add_argument("--channel", choices=["all", "finance", "tech", "sports", "ent", "world"],
                        default="all", help="频道 (默认全部)")
    args = parser.parse_args()

    channel_lid_map = {
        "all": [2509, 2510, 2511, 2669, 2514],
        "finance": [2509],
        "tech": [2510, 2515, 2970],
        "sports": [2511, 2968],
        "ent": [2669, 2513],
        "world": [2514],
    }
    lids = channel_lid_map[args.channel]

    print(f"正在爬取 {args.channel} 频道 {args.count} 条新闻...", flush=True)
    news = fetch_sina_news(args.count, lids)
    print(f"获取到 {len(news)} 条新闻", flush=True)

    indent = 2 if args.pretty else None
    json_str = json.dumps(news, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"已保存到 {args.output}", flush=True)
    else:
        # 终端可能不支持某些字符，安全输出
        try:
            print(json_str)
        except UnicodeEncodeError:
            print(json_str.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
