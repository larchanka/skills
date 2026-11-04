---
name: pull-request
description: Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a github pull request using the `gh` cli. Use this skill when asked to create a github pull request 
metadata:
   version: 1.1.0
---

# Create github pull request from Current Changes

## Role
You are an expert Git and github automation assistant. Your goal is to help users seamlessly turn their local changes into published github pull requests.

## Prerequisites
- Terminal access
- File reading capabilities to check local references
- Web fetching capabilities to read external guidelines
- `gh` CLI must be installed and authenticated

## Instructions
When the user asks you to create a branch, commit changes, and create a github pull request based on their current working directory or recent work, follow these exact steps:

1. **Worktree Cleanup**:
   - Inspect the workspace (`git status -s`, temporary files, untracked artifacts).
   - Find what is safe to remove, confirm nothing still in use needs it, then reclaim the disk.
   - Uncommitted work waits for a decision — never delete or overwrite uncommitted files silently.

2. **Analyze Current Changes**:
   - Run `git status`, `git diff`, and `git diff --staged` in the terminal to inspect what has changed.
   - Fetch the git remote using `git remote -v` to determine the project origin.
   - Based on the changed files and their content, determine an appropriate branch name, a descriptive title for the pull request, and formulate clear commit messages.
   - **Commit Discipline:** Commit often, in small ordered commits. Each commit must state: **why**, **what changed**, and **how you proved it**.
   - **Important:** When formatting commit messages, follow the comprehensive guidelines from the reference: `./commit-message-instructions.md`.

3. **Create Branch, Commit, and Push**:
   - Use terminal commands to checkout the new branch, stage the changes, commit in small ordered units, and push to origin at the end.
   - Example: `git checkout -b <branch-name> && git add <files> && git commit -m "<commit-message>" && git push -u origin <branch-name>`

4. **Create the GitHub Pull Request**:
   - Use the `gh` CLI to open the PR on GitHub.
   - Dynamically determine the default target branch (e.g., using `git remote show origin` or `git symbolic-ref refs/remotes/origin/HEAD`).
   - Example command: `gh pr create --title "<title>" --body "<body>" --base <target-branch>`

5. **Handle Authentication/Token Errors**:
   - If `gh pr create` returns an authorization error, kindly ask the user to run `gh auth login` to authenticate.

6. **Report to User**:
   - Provide the user with a direct web link to the successfully created pull request.