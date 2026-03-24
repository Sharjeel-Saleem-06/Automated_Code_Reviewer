"""
GitHub tool definitions for Claude's Tool Use / Function Calling.

This module defines:
1. JSON schemas that tell Claude what tools are available
2. The actual Python functions that execute when Claude calls a tool
3. Both simulated (demo) and real (production) modes

JD Coverage: "tool calling and function execution pipelines"
"""
import json
from typing import Optional


TOOL_DEFINITIONS = [
    {
        "name": "get_pr_diff",
        "description": (
            "Fetches the code diff (changes) from a GitHub Pull Request. "
            "Returns the raw unified diff showing added (+) and removed (-) lines."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "The GitHub repository owner (e.g., 'microsoft')"
                },
                "repo": {
                    "type": "string",
                    "description": "The repository name (e.g., 'vscode')"
                },
                "pr_number": {
                    "type": "integer",
                    "description": "The Pull Request number"
                }
            },
            "required": ["owner", "repo", "pr_number"]
        }
    },
    {
        "name": "get_pr_files",
        "description": (
            "Lists all files changed in a Pull Request with their change status "
            "(added, modified, removed) and line counts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {"type": "integer", "description": "PR number"}
            },
            "required": ["owner", "repo", "pr_number"]
        }
    },
    {
        "name": "post_review_comment",
        "description": (
            "Posts a review comment on a GitHub Pull Request. "
            "The comment body should be markdown-formatted."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {"type": "integer", "description": "PR number"},
                "body": {
                    "type": "string",
                    "description": "The markdown-formatted review comment"
                }
            },
            "required": ["owner", "repo", "pr_number", "body"]
        }
    }
]


def get_pr_diff(owner: str, repo: str, pr_number: int, github_token: Optional[str] = None) -> str:
    """Fetch PR diff. Uses real GitHub API if token provided, otherwise returns demo data."""
    if github_token and github_token != "your-github-personal-access-token":
        try:
            from github import Github
            g = Github(github_token)
            repository = g.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            files = pr.get_files()
            diff_parts = []
            for f in files:
                if f.patch:
                    diff_parts.append(f"diff --git a/{f.filename} b/{f.filename}\n{f.patch}")
            return "\n".join(diff_parts) if diff_parts else "No changes found."
        except Exception as e:
            return f"Error fetching PR: {e}"

    return _get_demo_diff()


def get_pr_files(owner: str, repo: str, pr_number: int, github_token: Optional[str] = None) -> str:
    """List files changed in a PR."""
    if github_token and github_token != "your-github-personal-access-token":
        try:
            from github import Github
            g = Github(github_token)
            repository = g.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            files_info = []
            for f in pr.get_files():
                files_info.append({
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions
                })
            return json.dumps(files_info, indent=2)
        except Exception as e:
            return f"Error: {e}"

    return json.dumps([
        {"filename": "api/routes.py", "status": "modified", "additions": 45, "deletions": 3},
        {"filename": "auth/login.py", "status": "modified", "additions": 22, "deletions": 0},
        {"filename": "utils/helpers.py", "status": "added", "additions": 38, "deletions": 0}
    ], indent=2)


def post_review_comment(owner: str, repo: str, pr_number: int, body: str,
                        github_token: Optional[str] = None) -> str:
    """Post review comment to PR."""
    if github_token and github_token != "your-github-personal-access-token":
        try:
            from github import Github
            g = Github(github_token)
            repository = g.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            pr.create_issue_comment(body)
            return f"Review comment posted to {owner}/{repo}#{pr_number}"
        except Exception as e:
            return f"Error posting comment: {e}"

    return f"[DEMO] Review comment would be posted to {owner}/{repo}#{pr_number}"


TOOL_EXECUTOR = {
    "get_pr_diff": get_pr_diff,
    "get_pr_files": get_pr_files,
    "post_review_comment": post_review_comment,
}


def _get_demo_diff() -> str:
    return '''diff --git a/api/routes.py b/api/routes.py
+from flask import Flask, request, jsonify
+import sqlite3
+import subprocess
+import pickle
+import hashlib
+
+app = Flask(__name__)
+DB_PASSWORD = "admin_super_secret_2024"
+
+@app.route('/users/<user_id>')
+def get_user(user_id):
+    conn = sqlite3.connect('production.db')
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    user = conn.execute(query).fetchone()
+    if user:
+        orders = []
+        for order_id in user['order_ids']:
+            order = conn.execute(f"SELECT * FROM orders WHERE id = '{order_id}'").fetchone()
+            orders.append(order)
+        user['orders'] = orders
+    return jsonify(user)
+
+@app.route('/admin/run', methods=['POST'])
+def run_command():
+    cmd = request.json.get('command')
+    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
+    return jsonify({"output": result.stdout})
+
+@app.route('/upload', methods=['POST'])
+def upload_data():
+    data = request.get_data()
+    obj = pickle.loads(data)
+    return jsonify({"status": "processed", "type": str(type(obj))})
+
+@app.route('/auth/login', methods=['POST'])
+def login():
+    username = request.form['username']
+    password = request.form['password']
+    hashed = hashlib.md5(password.encode()).hexdigest()
+    query = f"SELECT * FROM users WHERE username='{username}' AND password_hash='{hashed}'"
+    user = sqlite3.connect('production.db').execute(query).fetchone()
+    if user:
+        return jsonify({"token": "static_token_12345", "user": dict(user)})
+    return jsonify({"error": "Invalid credentials"}), 401
+
+@app.route('/search')
+def search():
+    term = request.args.get('q', '')
+    results = []
+    all_items = conn.execute("SELECT * FROM products").fetchall()
+    for item in all_items:
+        if term.lower() in item['name'].lower():
+            results.append(item)
+    return jsonify(results)'''
