#!/usr/bin/env python3
"""
GitHub Repository Analyzer
==========================
Analyzes GitHub repositories extracting commits, merges, PRs and other useful data
for productivity and code quality analysis.

Output:
    - commits_export.csv: All commits from all repositories
    - pull_requests_export.csv: All PRs from all repositories
    - contributors_summary.csv: Summary by contributor
    - repository_summary.csv: Summary by repository
    - quality_metrics.csv: Quality metrics by repository
    - productivity_analysis.csv: Productivity analysis by author
"""

import os
import csv
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
import re

# Try to import requests, otherwise use urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

DEFAULT_DAYS = 30
DEFAULT_OUTPUT_DIR = "github_export"
DEFAULT_REPOS_FILE = "repos.txt"
PER_PAGE = 100
VERBOSE = True

# =============================================================================
# TERMINAL COLORS
# =============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def print_banner():
    """Print the welcome banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   {Colors.GREEN}█▀▀ █ ▀█▀ █ █ █ █ █▄▄    ▄▀█ █▄ █ ▄▀█ █   █▄█ ▀█ █▀▀ █▀█ {Colors.CYAN}   ║
    ║   {Colors.GREEN}█▄█ █  █  █▀█ █▄█ █▄█    █▀█ █ ▀█ █▀█ █▄▄  █  █▄ ██▄ █▀▄ {Colors.CYAN}   ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║  {Colors.RESET}Analyze GitHub repositories and export data to CSV {Colors.CYAN}          ║
    ║  {Colors.RESET}for productivity and code quality analysis.       {Colors.CYAN}           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)

def print_features():
    """Print the tool features."""
    print(f"""
{Colors.BOLD}📊 WHAT THIS TOOL DOES:{Colors.RESET}

   {Colors.GREEN}✓{Colors.RESET} Analyzes {Colors.BOLD}commits{Colors.RESET} (author, date, lines added/removed, files changed)
   {Colors.GREEN}✓{Colors.RESET} Analyzes {Colors.BOLD}pull requests{Colors.RESET} (state, reviewers, merge time, approvals)
   {Colors.GREEN}✓{Colors.RESET} Analyzes {Colors.BOLD}issues{Colors.RESET} (bugs, enhancements, time to close)
   {Colors.GREEN}✓{Colors.RESET} Calculates {Colors.BOLD}quality metrics{Colors.RESET} (revert ratio, review coverage, commit quality)
   {Colors.GREEN}✓{Colors.RESET} Generates {Colors.BOLD}productivity analysis{Colors.RESET} for each contributor
   {Colors.GREEN}✓{Colors.RESET} Exports everything to {Colors.BOLD}CSV files{Colors.RESET} ready for analysis

{Colors.BOLD}📁 GENERATED FILES:{Colors.RESET}

   • commits_export.csv         - All commits with details
   • pull_requests_export.csv   - All PRs with metrics
   • issues_export.csv          - All issues
   • repository_summary.csv     - Statistics by repository
   • quality_metrics.csv        - Quality metrics
   • productivity_analysis.csv  - Productivity analysis by author
   • contributors_summary.csv   - Contributors summary
""")

def print_separator():
    print(f"{Colors.DIM}{'─' * 65}{Colors.RESET}")

def prompt_input(message: str, default: str = None) -> str:
    """Request input from user with default value support."""
    if default:
        prompt = f"{Colors.CYAN}▶{Colors.RESET} {message} [{Colors.DIM}{default}{Colors.RESET}]: "
    else:
        prompt = f"{Colors.CYAN}▶{Colors.RESET} {message}: "

    try:
        value = input(prompt).strip()
        return value if value else default
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.YELLOW}Operation cancelled.{Colors.RESET}")
        sys.exit(0)

def prompt_confirm(message: str, default: bool = True) -> bool:
    """Request yes/no confirmation."""
    default_str = "Y/n" if default else "y/N"
    prompt = f"{Colors.CYAN}▶{Colors.RESET} {message} [{default_str}]: "

    try:
        value = input(prompt).strip().lower()
        if not value:
            return default
        return value in ('y', 'yes', 's', 'si')
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.YELLOW}Operation cancelled.{Colors.RESET}")
        sys.exit(0)


class GitHubAnalyzer:
    """GitHub repository analyzer."""

    def __init__(self, token: str, output_dir: str, days: int, verbose: bool = True):
        self.token = token
        self.output_dir = output_dir
        self.verbose = verbose
        self.days = days
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Analyzer-Script"
        }
        self.since_date = datetime.now() - timedelta(days=days)
        self.request_count = 0
        self.start_time = None

        # Storage for aggregated data
        self.all_commits = []
        self.all_prs = []
        self.all_issues = []
        self.all_reviews = []
        self.contributor_stats = defaultdict(lambda: {
            "commits": 0,
            "additions": 0,
            "deletions": 0,
            "prs_opened": 0,
            "prs_merged": 0,
            "prs_reviewed": 0,
            "issues_opened": 0,
            "issues_closed": 0,
            "comments": 0,
            "repositories": set(),
            "first_activity": None,
            "last_activity": None,
            "commit_days": set(),
            "avg_commit_size": [],
        })
        self.repo_stats = {}

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def _log(self, message: str, level: str = "info", force: bool = False):
        """Log with verbose support."""
        if self.verbose or force or level == "error":
            timestamp = datetime.now().strftime("%H:%M:%S")

            colors = {
                "info": Colors.BLUE,
                "debug": Colors.DIM,
                "warn": Colors.YELLOW,
                "error": Colors.RED,
                "success": Colors.GREEN,
                "api": Colors.CYAN
            }

            prefixes = {
                "info": "INFO",
                "debug": "DEBUG",
                "warn": "WARN",
                "error": "ERROR",
                "success": "OK",
                "api": "API"
            }

            color = colors.get(level, "")
            prefix = prefixes.get(level, "INFO")

            print(f"{color}[{timestamp}] [{prefix}] {message}{Colors.RESET}")
            sys.stdout.flush()

    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """Make an HTTP request to the GitHub API."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            full_url = f"{url}?{param_str}"
        else:
            full_url = url

        self.request_count += 1

        # Log della richiesta
        short_url = url.replace(self.base_url, "").split("?")[0]
        self._log(f"Request #{self.request_count}: GET {short_url}", "api")

        try:
            if HAS_REQUESTS:
                response = requests.get(full_url, headers=self.headers, timeout=30)

                # Log rate limit info
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                limit = response.headers.get("X-RateLimit-Limit", "?")
                self._log(f"  -> Status: {response.status_code} | Rate limit: {remaining}/{limit}", "debug")

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    reset_time = response.headers.get("X-RateLimit-Reset", "")
                    if reset_time:
                        reset_dt = datetime.fromtimestamp(int(reset_time))
                        self._log(f"Rate limit reached! Reset at {reset_dt.strftime('%H:%M:%S')}", "error", force=True)
                    else:
                        self._log(f"Access denied: {short_url}", "error", force=True)
                    return None
                elif response.status_code == 404:
                    self._log(f"Resource not found: {short_url}", "warn")
                    return None
                else:
                    self._log(f"Error {response.status_code}: {short_url}", "error", force=True)
                    return None
            else:
                req = urllib.request.Request(full_url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode())
        except Exception as e:
            self._log(f"Request error: {e}", "error", force=True)
            return None

    def _paginate(self, url: str, params: dict = None) -> list:
        """Handle GitHub API request pagination."""
        all_items = []
        page = 1
        params = params or {}
        params["per_page"] = PER_PAGE

        short_url = url.replace(self.base_url, "")
        self._log(f"Starting pagination: {short_url}", "debug")

        while True:
            params["page"] = page
            items = self._make_request(url, params)

            if not items or len(items) == 0:
                break

            all_items.extend(items)
            self._log(f"  Page {page}: +{len(items)} items (total: {len(all_items)})", "debug")

            if len(items) < PER_PAGE:
                break

            page += 1

            # Safety limit
            if page > 50:
                self._log(f"Reached page limit (50) for {short_url}", "warn")
                break

        return all_items

    def parse_repo_url(self, repo: str) -> tuple:
        """Extract owner and repo name from URL or string."""
        repo = repo.replace("https://github.com/", "")
        repo = repo.replace("http://github.com/", "")
        repo = repo.rstrip("/")
        repo = repo.replace(".git", "")

        parts = repo.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None

    def fetch_commits(self, owner: str, repo: str) -> list:
        """Fetch all commits from the repository."""
        self._log(f"Fetching commits for {owner}/{repo}...", "info")
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"since": self.since_date.isoformat()}

        commits = self._paginate(url, params)
        processed = []
        total = len(commits)

        for idx, commit in enumerate(commits, 1):
            if not commit:
                continue

            sha = commit.get("sha", "")
            self._log(f"  Commit {idx}/{total}: {sha[:7]} - Recupero dettagli...", "debug")
            detail_url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
            detail = self._make_request(detail_url)

            stats = detail.get("stats", {}) if detail else {}
            files = detail.get("files", []) if detail else []

            commit_data = commit.get("commit", {})
            author_data = commit_data.get("author", {})
            committer_data = commit_data.get("committer", {})

            author_login = ""
            if commit.get("author"):
                author_login = commit["author"].get("login", "")

            committer_login = ""
            if commit.get("committer"):
                committer_login = commit["committer"].get("login", "")

            message = commit_data.get("message", "")
            is_merge = message.lower().startswith("merge")
            is_revert = message.lower().startswith("revert")

            file_types = defaultdict(int)
            for f in files:
                filename = f.get("filename", "")
                ext = os.path.splitext(filename)[1].lower()
                file_types[ext] += 1

            processed_commit = {
                "repository": f"{owner}/{repo}",
                "sha": sha,
                "short_sha": sha[:7] if sha else "",
                "author_name": author_data.get("name", ""),
                "author_email": author_data.get("email", ""),
                "author_login": author_login,
                "committer_name": committer_data.get("name", ""),
                "committer_email": committer_data.get("email", ""),
                "committer_login": committer_login,
                "date": author_data.get("date", ""),
                "message": message.split("\n")[0][:200],
                "full_message": message[:500],
                "additions": stats.get("additions", 0),
                "deletions": stats.get("deletions", 0),
                "total_changes": stats.get("total", 0),
                "files_changed": len(files),
                "is_merge_commit": is_merge,
                "is_revert": is_revert,
                "file_types": json.dumps(dict(file_types)),
                "url": commit.get("html_url", ""),
            }

            processed.append(processed_commit)

            if author_login:
                self._update_contributor_stats(author_login, processed_commit, "commit")

        self._log(f"Found {len(processed)} commits for {owner}/{repo}", "success")
        return processed

    def fetch_pull_requests(self, owner: str, repo: str) -> list:
        """Fetch all pull requests from the repository."""
        self._log(f"Fetching pull requests for {owner}/{repo}...", "info")
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {"state": "all", "sort": "updated", "direction": "desc"}

        prs = self._paginate(url, params)
        processed = []
        processed_count = 0

        for pr in prs:
            if not pr:
                continue

            created_at = pr.get("created_at", "")
            if created_at:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_date.replace(tzinfo=None) < self.since_date:
                    continue

            processed_count += 1
            pr_number = pr.get("number")
            self._log(f"  PR {processed_count} (#{pr_number}): Recupero reviews e commenti...", "debug")

            reviews_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            reviews = self._make_request(reviews_url) or []

            comments_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
            comments = self._make_request(comments_url) or []

            merged_at = pr.get("merged_at")
            time_to_merge = None
            if merged_at and created_at:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                merged = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                time_to_merge = (merged - created).total_seconds() / 3600

            labels = [l.get("name", "") for l in pr.get("labels", [])]

            user = pr.get("user", {})
            merged_by = pr.get("merged_by", {})

            processed_pr = {
                "repository": f"{owner}/{repo}",
                "number": pr_number,
                "title": pr.get("title", "")[:200],
                "state": pr.get("state", ""),
                "author_login": user.get("login", ""),
                "author_type": user.get("type", ""),
                "created_at": created_at,
                "updated_at": pr.get("updated_at", ""),
                "closed_at": pr.get("closed_at", ""),
                "merged_at": merged_at,
                "merged_by": merged_by.get("login", "") if merged_by else "",
                "is_merged": pr.get("merged", False),
                "draft": pr.get("draft", False),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
                "commits": pr.get("commits", 0),
                "comments": pr.get("comments", 0),
                "review_comments": pr.get("review_comments", 0),
                "time_to_merge_hours": round(time_to_merge, 2) if time_to_merge else None,
                "labels": ",".join(labels),
                "reviewers_count": len(set(r.get("user", {}).get("login", "") for r in reviews if r.get("user"))),
                "approvals": len([r for r in reviews if r.get("state") == "APPROVED"]),
                "changes_requested": len([r for r in reviews if r.get("state") == "CHANGES_REQUESTED"]),
                "base_branch": pr.get("base", {}).get("ref", ""),
                "head_branch": pr.get("head", {}).get("ref", ""),
                "url": pr.get("html_url", ""),
            }

            processed.append(processed_pr)

            author = user.get("login", "")
            if author:
                self._update_contributor_stats(author, processed_pr, "pr")

            for review in reviews:
                reviewer = review.get("user", {}).get("login", "")
                if reviewer and reviewer != author:
                    self._update_contributor_stats(reviewer, review, "review")

        self._log(f"Found {len(processed)} pull requests for {owner}/{repo}", "success")
        return processed

    def fetch_issues(self, owner: str, repo: str) -> list:
        """Fetch all issues from the repository (excluding PRs)."""
        self._log(f"Fetching issues for {owner}/{repo}...", "info")
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {"state": "all", "since": self.since_date.isoformat()}

        issues = self._paginate(url, params)
        processed = []

        for issue in issues:
            if not issue:
                continue

            if issue.get("pull_request"):
                continue

            user = issue.get("user", {})
            assignees = [a.get("login", "") for a in issue.get("assignees", [])]
            labels = [l.get("name", "") for l in issue.get("labels", [])]

            created_at = issue.get("created_at", "")
            closed_at = issue.get("closed_at")
            time_to_close = None
            if closed_at and created_at:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                time_to_close = (closed - created).total_seconds() / 3600

            processed_issue = {
                "repository": f"{owner}/{repo}",
                "number": issue.get("number"),
                "title": issue.get("title", "")[:200],
                "state": issue.get("state", ""),
                "author_login": user.get("login", ""),
                "created_at": created_at,
                "updated_at": issue.get("updated_at", ""),
                "closed_at": closed_at,
                "closed_by": issue.get("closed_by", {}).get("login", "") if issue.get("closed_by") else "",
                "comments": issue.get("comments", 0),
                "labels": ",".join(labels),
                "assignees": ",".join(assignees),
                "time_to_close_hours": round(time_to_close, 2) if time_to_close else None,
                "is_bug": any("bug" in l.lower() for l in labels),
                "is_enhancement": any("enhancement" in l.lower() or "feature" in l.lower() for l in labels),
                "url": issue.get("html_url", ""),
            }

            processed.append(processed_issue)

            author = user.get("login", "")
            if author:
                self._update_contributor_stats(author, processed_issue, "issue")

        self._log(f"Found {len(processed)} issues for {owner}/{repo}", "success")
        return processed

    def _update_contributor_stats(self, login: str, data: dict, data_type: str):
        """Update aggregated statistics for contributor."""
        stats = self.contributor_stats[login]
        stats["repositories"].add(data.get("repository", ""))

        date_str = data.get("date") or data.get("created_at") or data.get("submitted_at")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
                if stats["first_activity"] is None or date < stats["first_activity"]:
                    stats["first_activity"] = date
                if stats["last_activity"] is None or date > stats["last_activity"]:
                    stats["last_activity"] = date
            except:
                pass

        if data_type == "commit":
            stats["commits"] += 1
            stats["additions"] += data.get("additions", 0)
            stats["deletions"] += data.get("deletions", 0)
            stats["avg_commit_size"].append(data.get("total_changes", 0))
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    stats["commit_days"].add(date.strftime("%Y-%m-%d"))
                except:
                    pass

        elif data_type == "pr":
            stats["prs_opened"] += 1
            if data.get("is_merged"):
                stats["prs_merged"] += 1

        elif data_type == "review":
            stats["prs_reviewed"] += 1

        elif data_type == "issue":
            stats["issues_opened"] += 1
            if data.get("state") == "closed":
                stats["issues_closed"] += 1

    def calculate_repo_stats(self, owner: str, repo: str, commits: list, prs: list, issues: list) -> dict:
        """Calculate aggregated statistics for repository."""
        repo_name = f"{owner}/{repo}"

        total_commits = len(commits)
        merge_commits = len([c for c in commits if c.get("is_merge_commit")])
        revert_commits = len([c for c in commits if c.get("is_revert")])
        total_additions = sum(c.get("additions", 0) for c in commits)
        total_deletions = sum(c.get("deletions", 0) for c in commits)

        commit_authors = set(c.get("author_login") for c in commits if c.get("author_login"))

        total_prs = len(prs)
        merged_prs = len([p for p in prs if p.get("is_merged")])
        open_prs = len([p for p in prs if p.get("state") == "open"])

        merge_times = [p.get("time_to_merge_hours") for p in prs if p.get("time_to_merge_hours")]
        avg_time_to_merge = sum(merge_times) / len(merge_times) if merge_times else None

        total_issues = len(issues)
        closed_issues = len([i for i in issues if i.get("state") == "closed"])
        bug_issues = len([i for i in issues if i.get("is_bug")])

        commit_dates = set()
        for c in commits:
            if c.get("date"):
                try:
                    date = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
                    commit_dates.add(date.strftime("%Y-%m-%d"))
                except:
                    pass

        active_days = len(commit_dates)
        commits_per_day = total_commits / active_days if active_days > 0 else 0

        return {
            "repository": repo_name,
            "total_commits": total_commits,
            "merge_commits": merge_commits,
            "revert_commits": revert_commits,
            "regular_commits": total_commits - merge_commits - revert_commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "net_lines": total_additions - total_deletions,
            "unique_authors": len(commit_authors),
            "total_prs": total_prs,
            "merged_prs": merged_prs,
            "open_prs": open_prs,
            "pr_merge_rate": round(merged_prs / total_prs * 100, 2) if total_prs > 0 else 0,
            "avg_time_to_merge_hours": round(avg_time_to_merge, 2) if avg_time_to_merge else None,
            "total_issues": total_issues,
            "closed_issues": closed_issues,
            "open_issues": total_issues - closed_issues,
            "bug_issues": bug_issues,
            "issue_close_rate": round(closed_issues / total_issues * 100, 2) if total_issues > 0 else 0,
            "active_days": active_days,
            "commits_per_active_day": round(commits_per_day, 2),
            "analysis_period_days": self.days,
        }

    def calculate_quality_metrics(self, owner: str, repo: str, commits: list, prs: list) -> dict:
        """Calculate code quality metrics."""
        repo_name = f"{owner}/{repo}"

        total_commits = len(commits)
        reverts = len([c for c in commits if c.get("is_revert")])
        revert_ratio = reverts / total_commits * 100 if total_commits > 0 else 0

        commit_sizes = [c.get("total_changes", 0) for c in commits]
        avg_commit_size = sum(commit_sizes) / len(commit_sizes) if commit_sizes else 0
        large_commits = len([s for s in commit_sizes if s > 500])

        total_prs = len(prs)
        reviewed_prs = len([p for p in prs if p.get("reviewers_count", 0) > 0])
        review_coverage = reviewed_prs / total_prs * 100 if total_prs > 0 else 0

        approved_prs = len([p for p in prs if p.get("approvals", 0) > 0])
        approval_rate = approved_prs / total_prs * 100 if total_prs > 0 else 0

        changes_requested = len([p for p in prs if p.get("changes_requested", 0) > 0])
        changes_requested_ratio = changes_requested / total_prs * 100 if total_prs > 0 else 0

        draft_prs = len([p for p in prs if p.get("draft")])
        draft_ratio = draft_prs / total_prs * 100 if total_prs > 0 else 0

        good_messages = 0
        for c in commits:
            msg = c.get("message", "")
            if len(msg) > 10 and (msg[0].isupper() or re.match(r'^(feat|fix|docs|style|refactor|test|chore)', msg.lower())):
                good_messages += 1
        message_quality = good_messages / total_commits * 100 if total_commits > 0 else 0

        return {
            "repository": repo_name,
            "revert_ratio_pct": round(revert_ratio, 2),
            "avg_commit_size_lines": round(avg_commit_size, 2),
            "large_commits_count": large_commits,
            "large_commits_ratio_pct": round(large_commits / total_commits * 100, 2) if total_commits > 0 else 0,
            "pr_review_coverage_pct": round(review_coverage, 2),
            "pr_approval_rate_pct": round(approval_rate, 2),
            "pr_changes_requested_ratio_pct": round(changes_requested_ratio, 2),
            "draft_pr_ratio_pct": round(draft_ratio, 2),
            "commit_message_quality_pct": round(message_quality, 2),
            "quality_score": round(
                (100 - revert_ratio) * 0.2 +
                review_coverage * 0.25 +
                approval_rate * 0.2 +
                (100 - changes_requested_ratio) * 0.15 +
                message_quality * 0.2,
                2
            ),
        }

    def analyze_repository(self, repo: str, repo_index: int = 0, total_repos: int = 0):
        """Analyze a single repository."""
        owner, repo_name = self.parse_repo_url(repo)

        if not owner or not repo_name:
            self._log(f"Invalid repository format: {repo}", "error", force=True)
            return

        repo_progress = f"[{repo_index}/{total_repos}] " if total_repos > 0 else ""
        print(f"\n{'=' * 65}")
        self._log(f"{repo_progress}ANALYZING REPOSITORY: {owner}/{repo_name}", "info", force=True)
        print(f"{'=' * 65}")

        repo_start = datetime.now()

        commits = self.fetch_commits(owner, repo_name)
        prs = self.fetch_pull_requests(owner, repo_name)
        issues = self.fetch_issues(owner, repo_name)

        self.all_commits.extend(commits)
        self.all_prs.extend(prs)
        self.all_issues.extend(issues)

        self._log("Calculating repository statistics...", "info")
        repo_stats = self.calculate_repo_stats(owner, repo_name, commits, prs, issues)
        quality_metrics = self.calculate_quality_metrics(owner, repo_name, commits, prs)

        self.repo_stats[f"{owner}/{repo_name}"] = {
            "summary": repo_stats,
            "quality": quality_metrics,
        }

        elapsed = (datetime.now() - repo_start).total_seconds()
        self._log(
            f"Completed {owner}/{repo_name} in {elapsed:.1f}s: "
            f"{repo_stats['total_commits']} commits, {repo_stats['total_prs']} PRs, "
            f"{repo_stats['total_issues']} issues",
            "success", force=True
        )

    def generate_productivity_analysis(self) -> list:
        """Generate productivity analysis for each contributor."""
        productivity = []

        for login, stats in self.contributor_stats.items():
            if not login:
                continue

            total_commits = stats["commits"]
            active_days = len(stats["commit_days"])
            commits_per_day = total_commits / active_days if active_days > 0 else 0

            avg_commit_size = sum(stats["avg_commit_size"]) / len(stats["avg_commit_size"]) if stats["avg_commit_size"] else 0

            pr_merge_rate = stats["prs_merged"] / stats["prs_opened"] * 100 if stats["prs_opened"] > 0 else 0

            activity_span_days = 0
            if stats["first_activity"] and stats["last_activity"]:
                activity_span_days = (stats["last_activity"] - stats["first_activity"]).days + 1

            consistency = active_days / activity_span_days * 100 if activity_span_days > 0 else 0

            productivity.append({
                "contributor": login,
                "repositories": ",".join(stats["repositories"]),
                "repositories_count": len(stats["repositories"]),
                "total_commits": total_commits,
                "total_additions": stats["additions"],
                "total_deletions": stats["deletions"],
                "net_lines": stats["additions"] - stats["deletions"],
                "avg_commit_size": round(avg_commit_size, 2),
                "prs_opened": stats["prs_opened"],
                "prs_merged": stats["prs_merged"],
                "pr_merge_rate_pct": round(pr_merge_rate, 2),
                "prs_reviewed": stats["prs_reviewed"],
                "issues_opened": stats["issues_opened"],
                "issues_closed": stats["issues_closed"],
                "active_days": active_days,
                "commits_per_active_day": round(commits_per_day, 2),
                "first_activity": stats["first_activity"].isoformat() if stats["first_activity"] else "",
                "last_activity": stats["last_activity"].isoformat() if stats["last_activity"] else "",
                "activity_span_days": activity_span_days,
                "consistency_pct": round(consistency, 2),
                "productivity_score": round(
                    min(total_commits / 10, 30) +
                    min(stats["prs_merged"] * 5, 25) +
                    min(stats["prs_reviewed"] * 3, 20) +
                    min(consistency / 5, 15) +
                    min(len(stats["repositories"]) * 2, 10),
                    2
                ),
            })

        return sorted(productivity, key=lambda x: -x["productivity_score"])

    def export_to_csv(self):
        """Export all data to CSV files."""
        print(f"\n{Colors.BOLD}📁 Exporting to CSV...{Colors.RESET}")

        if self.all_commits:
            filepath = os.path.join(self.output_dir, "commits_export.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.all_commits[0].keys())
                writer.writeheader()
                writer.writerows(self.all_commits)
            print(f"   {Colors.GREEN}✓{Colors.RESET} commits_export.csv ({len(self.all_commits)} rows)")

        if self.all_prs:
            filepath = os.path.join(self.output_dir, "pull_requests_export.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.all_prs[0].keys())
                writer.writeheader()
                writer.writerows(self.all_prs)
            print(f"   {Colors.GREEN}✓{Colors.RESET} pull_requests_export.csv ({len(self.all_prs)} rows)")

        if self.all_issues:
            filepath = os.path.join(self.output_dir, "issues_export.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.all_issues[0].keys())
                writer.writeheader()
                writer.writerows(self.all_issues)
            print(f"   {Colors.GREEN}✓{Colors.RESET} issues_export.csv ({len(self.all_issues)} rows)")

        if self.repo_stats:
            summaries = [s["summary"] for s in self.repo_stats.values()]
            filepath = os.path.join(self.output_dir, "repository_summary.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=summaries[0].keys())
                writer.writeheader()
                writer.writerows(summaries)
            print(f"   {Colors.GREEN}✓{Colors.RESET} repository_summary.csv ({len(summaries)} rows)")

        if self.repo_stats:
            quality = [s["quality"] for s in self.repo_stats.values()]
            filepath = os.path.join(self.output_dir, "quality_metrics.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=quality[0].keys())
                writer.writeheader()
                writer.writerows(quality)
            print(f"   {Colors.GREEN}✓{Colors.RESET} quality_metrics.csv ({len(quality)} rows)")

        productivity = self.generate_productivity_analysis()
        if productivity:
            filepath = os.path.join(self.output_dir, "productivity_analysis.csv")
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=productivity[0].keys())
                writer.writeheader()
                writer.writerows(productivity)
            print(f"   {Colors.GREEN}✓{Colors.RESET} productivity_analysis.csv ({len(productivity)} rows)")

        if self.contributor_stats:
            contributors = []
            for login, stats in self.contributor_stats.items():
                if not login:
                    continue
                contributors.append({
                    "login": login,
                    "commits": stats["commits"],
                    "additions": stats["additions"],
                    "deletions": stats["deletions"],
                    "prs_opened": stats["prs_opened"],
                    "prs_merged": stats["prs_merged"],
                    "prs_reviewed": stats["prs_reviewed"],
                    "issues_opened": stats["issues_opened"],
                    "repositories_count": len(stats["repositories"]),
                    "repositories": ",".join(stats["repositories"]),
                })

            if contributors:
                filepath = os.path.join(self.output_dir, "contributors_summary.csv")
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=contributors[0].keys())
                    writer.writeheader()
                    writer.writerows(sorted(contributors, key=lambda x: -x["commits"]))
                print(f"   {Colors.GREEN}✓{Colors.RESET} contributors_summary.csv ({len(contributors)} rows)")

    def run(self, repositories: list):
        """Run the complete analysis on all repositories."""
        if not repositories:
            self._log("No repositories specified!", "error", force=True)
            return

        self.start_time = datetime.now()
        total_repos = len(repositories)

        print(f"\n{'=' * 65}")
        print(f"{Colors.BOLD}  🚀 STARTING ANALYSIS{Colors.RESET}")
        print(f"{'=' * 65}")
        print(f"   Repositories to analyze: {Colors.BOLD}{total_repos}{Colors.RESET}")
        print(f"   Analysis period: last {Colors.BOLD}{self.days}{Colors.RESET} days")
        print(f"   Period start date: {Colors.BOLD}{self.since_date.strftime('%Y-%m-%d')}{Colors.RESET}")
        print(f"   Output directory: {Colors.BOLD}{os.path.abspath(self.output_dir)}{Colors.RESET}")

        for idx, repo in enumerate(repositories, 1):
            try:
                self.analyze_repository(repo, idx, total_repos)
            except Exception as e:
                self._log(f"Analysis error for {repo}: {e}", "error", force=True)
                if self.verbose:
                    import traceback
                    traceback.print_exc()

        self.export_to_csv()

        total_time = (datetime.now() - self.start_time).total_seconds()

        print(f"\n{'=' * 65}")
        print(f"{Colors.GREEN}{Colors.BOLD}  ✅ ANALYSIS COMPLETED!{Colors.RESET}")
        print(f"{'=' * 65}")
        print(f"   ⏱️  Total time: {Colors.BOLD}{total_time:.1f}{Colors.RESET} seconds")
        print(f"   🌐 API requests: {Colors.BOLD}{self.request_count}{Colors.RESET}")
        print(f"   📝 Commits analyzed: {Colors.BOLD}{len(self.all_commits)}{Colors.RESET}")
        print(f"   🔀 Pull requests analyzed: {Colors.BOLD}{len(self.all_prs)}{Colors.RESET}")
        print(f"   🎫 Issues analyzed: {Colors.BOLD}{len(self.all_issues)}{Colors.RESET}")
        print(f"   👥 Contributors found: {Colors.BOLD}{len(self.contributor_stats)}{Colors.RESET}")
        print(f"\n   📁 Files generated in: {Colors.CYAN}{os.path.abspath(self.output_dir)}/{Colors.RESET}")


def load_repos_from_file(filepath: str) -> list:
    """Load list of repositories from file."""
    repos = []
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    repos.append(line)
    return repos


def create_sample_repos_file(filepath: str):
    """Create a sample repos.txt file."""
    sample_content = """# GitHub Repository Analyzer - Repository List
# Enter one repository per line
# Supported formats:
#   owner/repo
#   https://github.com/owner/repo
#
# Example:
# facebook/react
# microsoft/vscode
# https://github.com/torvalds/linux

"""
    with open(filepath, 'w') as f:
        f.write(sample_content)


def validate_token(token: str) -> bool:
    """Check if the GitHub token is valid."""
    if not token or len(token) < 10:
        return False

    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Analyzer-Script"
        }

        if HAS_REQUESTS:
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            return response.status_code == 200
        else:
            req = urllib.request.Request("https://api.github.com/user", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
    except:
        return False


def main():
    """Main interactive function."""

    # Banner and presentation
    print_banner()
    print_features()

    print_separator()
    print(f"{Colors.BOLD}⚙️  CONFIGURATION{Colors.RESET}\n")

    # 1. Request GitHub Token
    print(f"   To use this tool you need a {Colors.BOLD}GitHub Personal Access Token{Colors.RESET}.")
    print(f"   Create one at: {Colors.CYAN}https://github.com/settings/tokens{Colors.RESET}")
    print(f"   Required permissions: {Colors.DIM}repo (full control){Colors.RESET}\n")

    token = prompt_input("Enter your GitHub Token")

    if not token:
        print(f"\n{Colors.RED}❌ Token not provided. Cannot continue.{Colors.RESET}")
        sys.exit(1)

    # Validate token
    print(f"\n{Colors.DIM}   Validating token...{Colors.RESET}", end=" ")
    sys.stdout.flush()

    if validate_token(token):
        print(f"{Colors.GREEN}✓ Valid token!{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ Invalid token or insufficient permissions.{Colors.RESET}")
        if not prompt_confirm("Continue anyway?", default=False):
            sys.exit(1)

    # 2. Check/create repos.txt file
    print()
    repos_file = DEFAULT_REPOS_FILE

    if not os.path.exists(repos_file):
        print(f"   {Colors.YELLOW}⚠{Colors.RESET}  File {Colors.BOLD}{repos_file}{Colors.RESET} not found.")
        create_sample_repos_file(repos_file)
        print(f"   {Colors.GREEN}✓{Colors.RESET}  Created sample file: {Colors.BOLD}{repos_file}{Colors.RESET}")

    repos = load_repos_from_file(repos_file)

    if not repos:
        print(f"\n   {Colors.YELLOW}⚠{Colors.RESET}  No repositories found in {Colors.BOLD}{repos_file}{Colors.RESET}")
        print(f"   Add the repositories to analyze (one per line) and rerun the script.")
        print(f"\n   Example {repos_file} content:")
        print(f"   {Colors.DIM}owner/repo1")
        print(f"   owner/repo2")
        print(f"   https://github.com/org/project{Colors.RESET}")
        sys.exit(0)

    print(f"\n   {Colors.GREEN}✓{Colors.RESET}  Found {Colors.BOLD}{len(repos)}{Colors.RESET} repositories in {repos_file}:")
    for r in repos[:5]:
        print(f"      {Colors.DIM}• {r}{Colors.RESET}")
    if len(repos) > 5:
        print(f"      {Colors.DIM}... and {len(repos) - 5} more{Colors.RESET}")

    # 3. Ask for analysis period
    print()
    days_str = prompt_input(f"How many days do you want to analyze?", str(DEFAULT_DAYS))

    try:
        days = int(days_str)
        if days < 1:
            days = DEFAULT_DAYS
    except ValueError:
        days = DEFAULT_DAYS

    # 4. Output directory
    output_dir = DEFAULT_OUTPUT_DIR

    # 5. Confirm and start
    print()
    print_separator()
    print(f"\n{Colors.BOLD}📋 CONFIGURATION SUMMARY:{Colors.RESET}")
    print(f"   • Repositories: {Colors.BOLD}{len(repos)}{Colors.RESET}")
    print(f"   • Period: last {Colors.BOLD}{days}{Colors.RESET} days")
    print(f"   • Output: {Colors.BOLD}{output_dir}/{Colors.RESET}")
    print()

    if not prompt_confirm("Start the analysis?", default=True):
        print(f"\n{Colors.YELLOW}Analysis cancelled.{Colors.RESET}")
        sys.exit(0)

    # Start analysis
    analyzer = GitHubAnalyzer(token, output_dir, days, verbose=VERBOSE)
    analyzer.run(repos)

    print(f"\n{Colors.GREEN}Thank you for using GitHub Analyzer!{Colors.RESET}\n")


if __name__ == "__main__":
    main()
