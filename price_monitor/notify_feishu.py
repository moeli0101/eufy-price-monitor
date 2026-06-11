#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta


def get_tenant_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["tenant_access_token"]


def send_message(token, chat_id, content):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    payload = json.dumps({
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(content)
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result.get("code") == 0


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def calc_changes(history_path):
    history = load_json(history_path)
    if not history:
        return [], [], []

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    decreased, increased, new_promos = [], [], []

    for key, val in history.items():
        records = {r["date"]: r for r in val.get("price_history", []) if r.get("price")}
        if today not in records or yesterday not in records:
            continue

        t = records[today]
        y = records[yesterday]

        t_orig = t.get("original_price") or t.get("price")
        y_orig = y.get("original_price") or y.get("price")
        t_price = t.get("price")
        y_price = y.get("price")
        name = val.get("product_name", key)[:45]
        url = val.get("url", "")

        if t_orig and y_orig and t_orig != y_orig:
            diff = t_orig - y_orig
            if diff < 0:
                decreased.append({"name": name, "old": y_orig, "new": t_orig, "diff": diff, "url": url})
            else:
                increased.append({"name": name, "old": y_orig, "new": t_orig, "diff": diff, "url": url})

        if t_price and y_price and not t.get("is_on_sale") and y.get("is_on_sale"):
            new_promos.append({"name": name, "price": t_price, "orig": t_orig, "url": url})

    decreased.sort(key=lambda x: x["diff"])
    increased.sort(key=lambda x: -x["diff"])
    return decreased[:8], increased[:8], new_promos[:8]


def build_card(results_path, history_path):
    results = load_json(results_path) or []
    total = len(results)
    success = sum(1 for r in results if r.get("status") == "success" and r.get("price"))
    rate = round(success / total * 100) if total else 0
    date_str = datetime.now().strftime("%Y-%m-%d")

    decreased, increased, new_promos = calc_changes(history_path)

    def price_rows(items, kind):
        rows = []
        for p in items:
            if kind == "down":
                change = f"▼ A${abs(p['diff']):.0f}"
                line = f"**{p['name']}**\n${p['old']:.0f} → **${p['new']:.0f}**  {change}"
            elif kind == "up":
                change = f"▲ A${p['diff']:.0f}"
                line = f"**{p['name']}**\n${p['old']:.0f} → **${p['new']:.0f}**  {change}"
            else:
                line = f"**{p['name']}**\n原价 ${p['orig']:.0f} → 现价 **${p['price']:.0f}**"
            rows.append({"tag": "div", "text": {"tag": "lark_md", "content": line}})
            rows.append({"tag": "hr"})
        return rows

    elements = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"📊 **监控产品：{total} 个** | ✅ 成功：{success} 个（{rate}%）\n"
                    f"📅 更新日期：{date_str}\n"
                    f"🔗 [查看完整看板](https://moeli0101.github.io/eufy-price-monitor/)"
                )
            }
        },
        {"tag": "hr"}
    ]

    if decreased:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**🔻 MSRP 降价（{len(decreased)} 个）**"}})
        elements += price_rows(decreased, "down")

    if increased:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**🔺 MSRP 涨价（{len(increased)} 个）**"}})
        elements += price_rows(increased, "up")

    if new_promos:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**🏷️ 新增促销（{len(new_promos)} 个）**"}})
        elements += price_rows(new_promos, "promo")

    if not decreased and not increased and not new_promos:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "😊 今日无价格变动"}})

    return {
        "schema": "2.0",
        "body": {"elements": elements},
        "header": {
            "title": {"tag": "plain_text", "content": f"📦 JB Hi-Fi 价格监控日报 · {date_str}"},
            "template": "blue"
        }
    }


def main():
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    chat_id = os.environ.get("FEISHU_CHAT_ID")

    if not all([app_id, app_secret, chat_id]):
        print("❌ 缺少环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_CHAT_ID")
        sys.exit(1)

    results_path = "price_results_latest.json"
    history_path = "price_history.json"

    print("📨 获取飞书 token...")
    token = get_tenant_token(app_id, app_secret)

    print("📊 构建消息卡片...")
    card = build_card(results_path, history_path)

    print("📤 发送消息...")
    ok = send_message(token, chat_id, card)

    if ok:
        print("✅ 飞书通知发送成功")
    else:
        print("❌ 飞书通知发送失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
