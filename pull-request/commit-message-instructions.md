# Commit Message Guidelines

## Core Principles

- **Clarity**: Messages must clearly explain *what* changed and *why*.
- **Security**: 🚫 NEVER include secrets, API keys, credentials, or PII in commit messages.
- **Consistency**: Follow the Conventional Commits specification strictly.

## Format Structure

All commit messages MUST strictly follow this format:

```text
<type>(<scope>)[!]: <subject>

<body>

<impact-analysis>

<footer/metadata>
```

## 1. Header Line

The header must be **72 characters or less**.

For **Breaking Changes**, append `!` after the type/scope (e.g., `feat!: drop support for Node 12`) to signal a Major version bump.

### Types

Select the most specific type:

- `feat`: 🚀 New feature (correlates with MINOR in semantic versioning)
- `fix`: 🐛 Bug fix (correlates with PATCH in semantic versioning)
- `docs`: 📚 Documentation changes
- `style`: 💎 Code style/formatting (no logic change, whitespace, semi-colons)
- `refactor`: 📦 Code refactoring (no functional change, no api change)
- `perf`: ⚡ Performance improvements
- `test`: 🚨 Adding or updating tests
- `chore`: 🛠️ Maintenance tasks, dependencies, build scripts
- `ci`: ⚙️ CI/CD configuration changes
- `sec`: 🔒 Security fixes or improvements
- `revert`: ⏪ Revert a previous commit

### Scope (Optional)

Use the affected module/component (folder) name (lowercase, kebab-case):

- Core: `api`, `auth`, `data`, `utils`
- Infra: `ci`, `config`, `deploy`, `scripts`
- UI: `components`, `styles`, `views`, `assets`

**Constraints**:

- Select exactly **one** scope that best represents the primary change.
- If a change touches more than two distinct scopes, omit the scope entirely or use `core`.
- Do not use comma-separated scopes.

### Subject

- Use **imperative mood** ("Add feature" NOT "Added feature").
- Capitalize the first letter.
- Do not end with a period.
- Be concise but descriptive.

## 2. Body

- **Mandatory** for all `feat`, `fix`, and complex `refactor` changes.
- Separate from subject with a blank line.
- Wrap lines at 72 characters.
- Start with "This change..." to contextualize the description.
- Explain the **motivation** for the change and contrast with previous behavior.
- Use bullet points (`-`) for lists.

## 3. Impact Analysis

Instead of listing file changes, list significant side effects or impacts that may not be visible in the code diff.

- **Migrations**: Database schema changes or data migrations?
- **Deprecations**: Are any APIs or features deprecated?
- **Dependencies**: New external libraries added?
- **Configuration**: Changes to ENV variables or config files?

## 4. Footer / Metadata

- Reference issue tracker IDs explicitly (e.g., Jira, GitHub Issues).
- Format: `Ref: #123` or `Fixes: ISSUE-123`.
- Mention breaking changes if any: `BREAKING CHANGE: <description>\`.

### Example

```text
feat(auth): Add login rate limiting

Implement rate limiting on the login endpoint to prevent brute
force attacks. Users are now locked out after 5 failed attempts.

Impact:
- Configuration: Added `SECURITY_MAX_ATTEMPTS` to config.yaml
- Security: Enforces 5-attempt limit per IP

Ref: ISSUE-456
```