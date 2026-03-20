#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单上传脚本 - 上传所有改进到GitHub
用法: python3 upload_to_github.py YOUR_GITHUB_TOKEN
"""

import sys
import requests
import base64
from datetime import datetime

def upload_to_github(token):
    """上传所有改进的文件到GitHub"""

    USERNAME = "moeli0101"
    REPO = "eufy-price-monitor"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 测试token
    print("🔐 验证Token...")
    response = requests.get("https://api.github.com/user", headers=headers)

    if response.status_code != 200:
        print("❌ Token无效！请生成新的token")
        print("   访问: https://github.com/settings/tokens/new")
        print("   权限: 勾选 repo (所有子选项)")
        return False

    user = response.json()
    print(f"✅ Token有效 (用户: {user['login']})")

    # 要上传的文件列表
    files = [
        ('product_classifier.py', '✨ 新增：统一产品分类器'),
        ('validate_data.py', '🔍 新增：数据验证脚本'),
        ('daily_price_refresh.py', '🔧 改进：使用统一分类+重试机制'),
        ('docs/index.html', '🌐 更新：Swann筛选+10款门铃'),
        ('price_results_latest.json', '📊 更新：修正Swann门铃分类'),
    ]

    print(f"\n📤 开始上传 {len(files)} 个文件...\n")

    success_count = 0

    for file_path, description in files:
        print(f"⬆️  {file_path}...")

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 获取当前文件SHA（如果存在）
            url = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/{file_path}"
            response = requests.get(url, headers=headers)
            sha = response.json().get('sha') if response.status_code == 200 else None

            # Base64编码
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

            # 上传
            data = {
                "message": description,
                "content": encoded_content,
                "branch": "main"
            }
            if sha:
                data["sha"] = sha

            response = requests.put(url, headers=headers, json=data)

            if response.status_code in [200, 201]:
                print(f"   ✅ 成功")
                success_count += 1
            else:
                print(f"   ❌ 失败: {response.status_code}")
                print(f"      {response.json().get('message', 'Unknown error')}")

        except Exception as e:
            print(f"   ❌ 错误: {e}")

        print()

    # 总结
    print("=" * 70)
    if success_count == len(files):
        print(f"🎉 成功！所有 {len(files)} 个文件已上传")
        print(f"\n🌐 网站: https://{USERNAME}.github.io/{REPO}/")
        print("⏱️  请等待1-2分钟后刷新页面")
        print("\n✅ 系统加固完成:")
        print("   • 统一分类器确保产品正确分类")
        print("   • Swann门铃不会再被错误分类")
        print("   • 抓取失败自动重试3次")
        print("   • 每次更新自动验证数据质量")
        return True
    else:
        print(f"⚠️  部分成功: {success_count}/{len(files)} 文件已上传")
        print(f"   请检查失败的文件并重试")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 upload_to_github.py YOUR_GITHUB_TOKEN")
        print("\n如何获取Token:")
        print("1. 访问: https://github.com/settings/tokens/new")
        print("2. Note: eufy-price-monitor-upload")
        print("3. 勾选权限: repo (所有子选项)")
        print("4. 点击 Generate token，复制token")
        print("\n然后运行:")
        print("python3 upload_to_github.py ghp_xxxxxxxxxxxx")
        sys.exit(1)

    token = sys.argv[1]
    success = upload_to_github(token)
    sys.exit(0 if success else 1)
