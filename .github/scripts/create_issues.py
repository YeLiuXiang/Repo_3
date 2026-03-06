#!/usr/bin/env python3
"""
Create GitHub Issues from tasks.md
Usage: python create_issues.py --repo OWNER/REPO --tasks-file PATH/TO/tasks.md
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date


PHASE_MAP = {
    "阶段一": "阶段一：环境搭建",
    "阶段二": "阶段二：基础模块",
    "阶段三": "阶段三：US-07 — 用户账号与权限管理",
    "阶段四": "阶段四：US-01 — 配置并执行关键词数据采集任务",
    "阶段五": "阶段五：US-02 — 查看内容热度趋势分析",
    "阶段六": "阶段六：US-03 — 品牌关键词情感分析",
    "阶段七": "阶段七：US-05 — 采集任务定时调度",
    "阶段八": "阶段八：US-06 — 热门内容榜单浏览",
    "阶段九": "阶段九：US-04 — 多平台数据对比报告导出",
    "阶段十": "阶段十：Streamlit Dashboard 展示层",
    "阶段十一": "阶段十一：收尾与横向关注点",
}

US_TITLES = {
    "US1": "US-01 — 配置并执行关键词数据采集任务",
    "US2": "US-02 — 查看内容热度趋势分析",
    "US3": "US-03 — 品牌关键词情感分析",
    "US4": "US-04 — 多平台数据对比报告导出",
    "US5": "US-05 — 采集任务定时调度",
    "US6": "US-06 — 热门内容榜单浏览",
    "US7": "US-07 — 用户账号与权限管理",
}

FEATURE_DIR = "specs/social-media-collect-analyze"


def parse_tasks(tasks_file):
    """Parse tasks.md and return list of task dicts."""
    with open(tasks_file, encoding="utf-8") as f:
        content = f.read()

    tasks = []
    current_phase = ""
    in_code_block = False

    for line in content.splitlines():
        # Track fenced code blocks to skip example lines
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Detect phase headers
        phase_match = re.match(r"^## (阶段[一二三四五六七八九十]+)", line)
        if phase_match:
            phase_key = phase_match.group(1)
            current_phase = PHASE_MAP.get(phase_key, phase_key)
            continue

        # Match task lines: - [ ] T001 [optional flags] description
        task_match = re.match(r"^- \[ \] (T\d+)((?:\s+\[(?:P|US\d+)\])*)\s+(.+)$", line)
        if not task_match:
            continue

        task_id = task_match.group(1)
        flags_str = task_match.group(2)
        description = task_match.group(3).strip()

        # Parse flags
        parallel = "[P]" in flags_str
        us_tags = re.findall(r"\[US(\d+)\]", flags_str)

        # Extract file path from description (路径：...)
        path_match = re.search(r"路径：([^）)]+)", description)
        file_path = path_match.group(1).strip() if path_match else ""

        # Build US label string
        us_labels = [f"US{u}" for u in us_tags]
        if us_labels:
            us_str = "、".join(US_TITLES[u] for u in us_labels if u in US_TITLES)
        else:
            us_str = "无"

        tasks.append(
            {
                "id": task_id,
                "description": description,
                "file_path": file_path,
                "phase": current_phase,
                "parallel": parallel,
                "us_labels": us_labels,
                "us_str": us_str,
            }
        )

    return tasks


def gh_api(method, path, data=None):
    """Call GitHub API via gh CLI."""
    cmd = ["gh", "api", "--method", method, path]
    if data:
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    cmd += ["-f", f"{key}[]={item}"]
            else:
                cmd += ["-f", f"{key}={value}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return result.stdout, None


def ensure_label(repo, label_name, color, description):
    """Create label if it doesn't exist."""
    data, err = gh_api("GET", f"/repos/{repo}/labels/{label_name}")
    if data and "name" in data:
        print(f"  Label '{label_name}' already exists.")
        return True

    print(f"  Creating label '{label_name}'...")
    data, err = gh_api(
        "POST",
        f"/repos/{repo}/labels",
        {"name": label_name, "color": color, "description": description},
    )
    if err:
        print(f"  ERROR creating label: {err}", file=sys.stderr)
        return False
    print(f"  Label '{label_name}' created.")
    return True


def get_existing_issues(repo):
    """Get all existing open issues by title."""
    existing = {}
    page = 1
    while True:
        result = subprocess.run(
            [
                "gh", "api",
                f"/repos/{repo}/issues?state=open&per_page=100&page={page}",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            break
        issues = json.loads(result.stdout)
        if not issues:
            break
        for issue in issues:
            # Skip pull requests (the issues endpoint also returns PRs)
            if "pull_request" not in issue:
                existing[issue["title"]] = issue["number"]
        if len(issues) < 100:
            break
        page += 1
    return existing


def build_issue_body(task, today):
    """Build the issue body markdown."""
    us_section = task["us_str"]
    file_path = task["file_path"] if task["file_path"] else "（见任务描述）"

    body = f"""## 任务描述

{task['description']}

**目标文件**：`{file_path}`
**所属阶段**：{task['phase']}
**关联用户故事**：{us_section}

---

## 完成定义（DoD）

- [ ] 代码已提交 PR 并通过 Code Review
- [ ] 单元测试覆盖率 ≥ 80%（如适用）
- [ ] CI 全部检查通过
- [ ] 无 CRITICAL 级别的 Bug

---

## 相关资源

- 📋 PRD：`{FEATURE_DIR}/prd.md`
- 🏗️ 技术方案：`{FEATURE_DIR}/plan.md`
- 📂 功能目录：`{FEATURE_DIR}/`

---
*由 proj.taskstoissues 自动创建 • {today}*"""
    return body


def create_issue(repo, title, body, labels):
    """Create a single GitHub issue."""
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
        "--label", ",".join(labels),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr
    # gh issue create returns the URL of the new issue
    url = result.stdout.strip()
    # Extract issue number from URL
    m = re.search(r"/issues/(\d+)$", url)
    number = int(m.group(1)) if m else None
    return number, None


def main():
    parser = argparse.ArgumentParser(description="Create GitHub Issues from tasks.md")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument(
        "--tasks-file",
        default="specs/social-media-collect-analyze/tasks.md",
        help="Path to tasks.md",
    )
    args = parser.parse_args()

    repo = args.repo
    tasks_file = args.tasks_file
    today = date.today().isoformat()

    print(f"\n🚀 Starting issue creation for {repo}")
    print(f"📄 Tasks file: {tasks_file}\n")

    # Step 1: Parse tasks
    tasks = parse_tasks(tasks_file)
    print(f"✅ Parsed {len(tasks)} tasks from {tasks_file}\n")

    # Step 2: Ensure 'task' label exists
    print("🏷️  Checking labels...")
    ensure_label(repo, "task", "5319E7", "Tracked implementation task")
    print()

    # Step 3: Get existing issues (for deduplication)
    print("🔍 Fetching existing issues...")
    existing = get_existing_issues(repo)
    print(f"   Found {len(existing)} existing open issues\n")

    # Step 4: Create issues
    created = 0
    skipped = 0
    failed = 0

    for task in tasks:
        task_num = task["id"][1:]  # Remove 'T' prefix, keep number
        title = f"[TASK] T-{task_num}: {task['description']}"
        # Truncate title if too long (GitHub limit is 256 chars)
        if len(title) > 256:
            title = title[:253] + "..."

        if title in existing:
            print(f"  ⏭️  SKIP #{existing[title]} {task['id']}: already exists")
            skipped += 1
            continue

        body = build_issue_body(task, today)
        number, err = create_issue(repo, title, body, ["task"])

        if err:
            print(f"  ❌ FAIL {task['id']}: {err.strip()}", file=sys.stderr)
            failed += 1
        else:
            print(f"  ✅ #{number} {task['id']}: {task['description'][:60]}")
            created += 1

    # Step 5: Summary
    print(f"\n{'='*60}")
    print(f"✅ 云端同步完成")
    print(f"📝 Issues: 成功 {created} 个，跳过 {skipped} 个，失败 {failed} 个")
    print(f"🔗 Issues: https://github.com/{repo}/issues?label=task")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
