# AI Changelog Insights 🤖

A real-time, autonomous dashboard that aggregates and summarizes daily updates from top-performing AI repositories.

https://makary-kleinschmidt.github.io/ai-changelog-insights/

## 🚀 Key Features

-   **Real-Time Aggregation**: Fetches fresh data directly from GitHub API, bypassing caches.
-   **Smart Filtering**: Identifies high-impact AI repositories with updates strictly from the **current day**.
-   **Intelligent Fallback**: Scans up to 200 active repositories to secure 9 daily updates.
-   **Concise Summaries**: Uses Gemini 3 Flash Preview to extract key features, fixes, and breaking changes.
-   **Resilient Architecture**: Automated retries on 503/429/504 errors with tiered model fallback (Gemini 3 → 2.5 → 2.0). Truncated JSON repair for cut-off responses.
-   **Intelligent Insights**: Provides a 3-level "Try It Out" section (Beginner, Intermediate, Advanced).
-   **Responsive Design**: Dark/Light mode supported, includes collapsed accordion sections for clean layout.
-   **Automated Pipeline**: Runs daily at 23:55 UTC via GitHub Actions.

See [CHANGELOG.md](./CHANGELOG.md) for recent updates.

## 🛠️ Setup & Installation

### Prerequisites

-   **Python 3.12+**
-   **uv** (Fast Python package manager)
-   **Git**

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ai-changelog-insights.git
    cd ai-changelog-insights
    ```

2.  **Initialize**:
    ```bash
    uv sync
    ```

3.  **Configure Secrets**:
    Create a `.env` file:
    ```env
    GEMINI_API_KEY=your_google_ai_studio_key_here
    GH_ACCESS_TOKEN=ghp_your_github_token  # REQUIRED for rate limits
    ```

## 🏃‍♂️ Usage

### Manual Run (Today's Updates)
```bash
uv run python -m src.main
```

### Run for Specific Date
```bash
uv run python -m src.main --date 2026-02-26
```

### Force Regeneration
```bash
uv run python -m src.main --date 2026-02-26 --force
```

## 📦 Deployment Plan

### 1. Environment Variables
-   `GEMINI_API_KEY`: API key for Google AI Studio.
-   `GH_ACCESS_TOKEN`: Personal Access Token (Classic) with `public_repo` scope.

### 2. CI/CD Pipeline
The project uses GitHub Actions (`.github/workflows/daily-update.yml`) for continuous delivery.
-   **Trigger**: Scheduled cron job at 23:55 UTC daily.
-   **Process**:
    1.  Checkout code.
    2.  Install `uv` and dependencies.
    3.  Run `python -m src.main` to fetch fresh data and generate `site/index.html`.
    4.  Deploy `site/` directory to `gh-pages` branch.

### 3. Monitoring & Alerts
-   **GitHub Actions**: Check the "Actions" tab for run status.
-   **Log Analysis**: The build logs output detailed progress:
    -   `[5/100] Checking repo-name...`
    -   `✅ FOUND UPDATE`
    -   `⚠️ Reached check limit`
-   **Health Check**: A simple uptime monitor (e.g., UptimeRobot) can ping the GitHub Pages URL to ensure 200 OK status.

### 4. Automated Verification
Run the verification script to ensure the logic works as expected without API calls (mocked):
```bash
uv run python -m pytest tests/test_flow.py
```

## 🛡️ Architecture

-   **Fetcher (`src/github_client.py`)**:
    -   Uses `tenacity` for exponential backoff retries.
    -   Filters repositories by `pushed_at` timestamp.
    -   Iterates through paginated results until quota is met.
-   **Summarizer (`src/summarizer.py`)**:
    -   Uses Gemini 3 Flash Preview (with 2.5/2.0 fallback) to parse CHANGELOGs.
    -   Implements 5 RPM rate limiting (12s delay) and retries on 503/429/504.
    -   Returns structured JSON for What's New, Why It's Important, and Try It Out (3 levels).
    -   Includes truncated JSON repair for cut-off LLM responses.
-   **Generator (`src/main.py`)**:
    -   Orchestrates the loop.
    -   Generates static HTML with Jinja2.

---
*Powered by Gemini 3 Flash Preview and GitHub API.*
