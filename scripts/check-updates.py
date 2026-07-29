#!/usr/bin/env python3
"""
mia-toolbox 更新检测脚本

用途：
- 遍历 tool-state.json 里的所有工具仓库
- 通过 gh CLI 查询每个仓库 main 分支的最新 commit
- 与 lastSha 对比，如有变化：
    1. 更新 lastSha / lastUpdated
    2. 把新增的 commit 摘要 append 到 autoChangelog
    3. checkedAt 更新为今天
- 有任何变化则 git commit + push 到 mia-toolbox 仓库
- 无变化时脚本沉默退出

设计要点：
- autoChangelog 最多保留最近 20 条，避免文件无限增长
- 只统计与上次记录 SHA 之间的新 commit（用 gh api 的 compare API）
- 完全依赖 gh CLI 已登录状态
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "tool-state.json"
MAX_AUTO_CHANGELOG = 20

# 本地时区：中国大陆 UTC+8
CN_TZ = timezone(timedelta(hours=8))


def today_str() -> str:
    return datetime.now(CN_TZ).strftime("%Y-%m-%d")


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def gh_api(path: str) -> dict:
    out = run(["gh", "api", path])
    return json.loads(out)


def get_new_commits(repo: str, base_sha: str) -> list[dict]:
    """获取 base_sha..main 之间的新 commit（不含 base_sha 自己）。"""
    try:
        data = gh_api(f"/repos/{repo}/compare/{base_sha}...main")
    except RuntimeError:
        # 兜底：base_sha 已被 rebase/删除，退化到取最近 5 条
        raw = gh_api(f"/repos/{repo}/commits?per_page=5")
        return [
            {
                "sha": c["sha"],
                "msg": c["commit"]["message"].split("\n")[0],
                "date": c["commit"]["author"]["date"][:10],
            }
            for c in raw
        ]

    commits = []
    for c in data.get("commits", []):
        commits.append(
            {
                "sha": c["sha"],
                "msg": c["commit"]["message"].split("\n")[0],
                "date": c["commit"]["author"]["date"][:10],
            }
        )
    return commits


def check_all() -> bool:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    changed_any = False
    today = today_str()
    change_report = []

    for slug, info in state["tools"].items():
        repo = info["repo"]
        base_sha = info["lastSha"]
        try:
            latest = gh_api(f"/repos/{repo}/commits/main")
        except RuntimeError as e:
            print(f"[WARN] {slug}: fetch latest failed: {e}", file=sys.stderr)
            continue

        latest_sha = latest["sha"]
        if latest_sha == base_sha:
            print(f"[SKIP] {slug}: no changes")
            continue

        new_commits = get_new_commits(repo, base_sha)
        if not new_commits:
            # 有 SHA 变化但 compare 返回空，可能是 force-push / rebase
            new_commits = [
                {
                    "sha": latest_sha,
                    "msg": latest["commit"]["message"].split("\n")[0],
                    "date": latest["commit"]["author"]["date"][:10],
                }
            ]

        # 新条目按日期倒序 append，最新在最前
        auto = info.get("autoChangelog", [])
        # 反转让最新的在最前，然后合并原有的
        prepend = [{"date": c["date"], "msg": c["msg"]} for c in reversed(new_commits)]
        info["autoChangelog"] = (prepend + auto)[:MAX_AUTO_CHANGELOG]
        info["lastSha"] = latest_sha
        info["lastUpdated"] = today

        change_report.append(f"{slug}: +{len(new_commits)} commit(s)")
        changed_any = True

    state["checkedAt"] = today

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return changed_any, change_report


def git_commit_and_push(report: list[str]) -> None:
    run(["git", "-C", str(REPO_ROOT), "add", "tool-state.json"])
    # 只有 state 文件真的有 diff 才 commit
    diff = run(
        ["git", "-C", str(REPO_ROOT), "diff", "--cached", "--quiet"], check=False
    )
    # diff --quiet 有变化时 exit code 非 0 → run() 用 check=False，返回空 stdout
    # 我们改用 status 判断
    status = run(["git", "-C", str(REPO_ROOT), "status", "--porcelain"])
    if "tool-state.json" not in status:
        print("[INFO] no actual diff, skip commit")
        return

    summary = " | ".join(report) if report else "auto check"
    msg = f"chore(auto): daily update check\n\n{summary}"
    run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "-c",
            "user.email=mia-bot@local",
            "-c",
            "user.name=mia-toolbox-bot",
            "commit",
            "-m",
            msg,
        ]
    )
    run(["git", "-C", str(REPO_ROOT), "push"])
    print("[OK] pushed:", msg.splitlines()[0])


def main() -> int:
    changed, report = check_all()
    if changed:
        print("[CHANGES]", "; ".join(report))
        git_commit_and_push(report)
    else:
        # 即便没有工具变化，checkedAt 也已更新，若门户希望展示"今日已检查"再决定要不要提交
        # 目前策略：无工具变化则不提交，避免 mia-toolbox 每天都长一条 commit
        print("[QUIET] no tool updated today")
    return 0


if __name__ == "__main__":
    sys.exit(main())
