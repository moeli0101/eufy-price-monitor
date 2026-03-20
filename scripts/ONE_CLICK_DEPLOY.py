#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键部署脚本 - 只需运行一次，以后完全自动！
"""

import requests
import json
import base64
import os
from datetime import datetime

def deploy_to_github(token):
    """使用GitHub API自动部署"""

    username = "moeli0101"
    repo_name = "eufy-price-monitor"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    print("\n" + "=" * 70)
    print("🚀 开始自动部署...")
    print("=" * 70)

    # 1. 检查仓库是否存在，不存在则创建
    print("\n📦 步骤1: 检查/创建GitHub仓库...")
    repo_url = f"https://api.github.com/repos/{username}/{repo_name}"
    response = requests.get(repo_url, headers=headers)

    if response.status_code == 404:
        # 创建仓库
        create_url = "https://api.github.com/user/repos"
        data = {
            "name": repo_name,
            "description": "eufy澳洲价格监控系统 - 自动更新",
            "private": False,
            "auto_init": True
        }
        response = requests.post(create_url, headers=headers, json=data)
        if response.status_code == 201:
            print("   ✅ 仓库创建成功！")
        else:
            print(f"   ❌ 创建失败: {response.json()}")
            return False
    else:
        print("   ✅ 仓库已存在")

    # 2. 上传文件
    print("\n📤 步骤2: 上传文件到GitHub...")

    files_to_upload = [
        ("docs/index.html", "eufy_price_monitor_standalone.html"),
        ("README.md", "README.md"),
        (".github/workflows/update-prices.yml", ".github/workflows/update-prices.yml"),
        ("price_dashboard_v5.html", "price_dashboard_v5.html"),
        ("daily_price_refresh.py", "daily_price_refresh.py"),
        ("price_results_latest.json", "price_results_latest.json"),
    ]

    for github_path, local_file in files_to_upload:
        if not os.path.exists(local_file):
            print(f"   ⚠️  跳过不存在的文件: {local_file}")
            continue

        with open(local_file, 'rb') as f:
            content = base64.b64encode(f.read()).decode()

        url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{github_path}"

        # 检查文件是否存在
        check_response = requests.get(url, headers=headers)

        data = {
            "message": f"Update {github_path}",
            "content": content
        }

        if check_response.status_code == 200:
            # 文件存在，需要提供sha
            data["sha"] = check_response.json()["sha"]

        response = requests.put(url, headers=headers, json=data)

        if response.status_code in [200, 201]:
            print(f"   ✅ {github_path}")
        else:
            print(f"   ❌ {github_path}: {response.status_code}")

    # 3. 启用GitHub Pages
    print("\n🌐 步骤3: 启用GitHub Pages...")
    pages_url = f"https://api.github.com/repos/{username}/{repo_name}/pages"

    pages_data = {
        "source": {
            "branch": "main",
            "path": "/docs"
        }
    }

    # 先检查是否已启用
    check_pages = requests.get(pages_url, headers=headers)

    if check_pages.status_code == 404:
        # 启用GitHub Pages
        response = requests.post(pages_url, headers=headers, json=pages_data)
        if response.status_code == 201:
            print("   ✅ GitHub Pages已启用！")
        else:
            print(f"   ⚠️  GitHub Pages启用失败（可能需要手动启用）")
    else:
        print("   ✅ GitHub Pages已启用")

    print("\n" + "=" * 70)
    print("🎉 部署完成！")
    print("=" * 70)
    print(f"\n🔗 你的网站地址：")
    print(f"   https://{username}.github.io/{repo_name}/")
    print("\n⏰ 自动更新：")
    print("   每天UTC 18:00（北京时间凌晨2点）自动更新价格")
    print("\n✅ 你什么都不用做，完全自动化！")
    print("=" * 70)

    return True

def main():
    print("=" * 70)
    print("🎯 eufy价格监控 - 一键部署")
    print("=" * 70)
    print("\n这个脚本会自动：")
    print("  1. 在GitHub创建/更新仓库")
    print("  2. 上传所有文件")
    print("  3. 启用GitHub Pages")
    print("  4. 配置每日自动更新")
    print("\n你只需要提供一个GitHub token（只用这一次）")
    print("=" * 70)

    # 检查是否已有token
    token_file = ".github_token"
    token = None

    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read().strip()
        print("\n✅ 找到已保存的token")
    else:
        print("\n📋 获取GitHub token：")
        print("   1. 打开: https://github.com/settings/tokens/new")
        print("   2. Note: eufy-price-monitor")
        print("   3. Expiration: 90 days")
        print("   4. 勾选: repo (所有)")
        print("   5. 点击: Generate token")
        print("   6. 复制token（ghp_开头的字符串）")
        print("\n请粘贴你的GitHub token:")
        token = input().strip()

        # 保存token
        with open(token_file, 'w') as f:
            f.write(token)
        print("✅ Token已保存")

    # 开始部署
    success = deploy_to_github(token)

    if not success:
        print("\n❌ 部署失败，请检查token是否有效")
        if os.path.exists(token_file):
            os.remove(token_file)

if __name__ == "__main__":
    os.chdir("/Users/anker/Desktop/feishu_bot")
    main()
