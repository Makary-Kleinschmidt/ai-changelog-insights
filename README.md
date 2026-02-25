# AI Changelog Insights 🤖

A real-time, autonomous dashboard that aggregates and summarizes daily updates from top-performing AI repositories.

## 🚀 Key Features

-   **Real-Time Aggregation**: Fetches fresh data directly from GitHub API, bypassing caches.
-   **Smart Filtering**: Identifies high-impact AI repositories with updates strictly from the **current day**.
-   **Intelligent Fallback**: Scans up to 100 active repositories to ensure 10 distinct daily updates are found.
-   **Concise Summaries**: Uses OpenRouter LLM to extract key features, fixes, and breaking changes.
-   **Responsive Design**: Dark/Light mode supported, < 2s load time.
-   **Automated Pipeline**: Runs daily at 23:55 UTC via GitHub Actions.

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
    OPENROUTER_API_KEY=sk-or-v1-your-key-here
    GITHUB_TOKEN=ghp_your_github_token  # REQUIRED for rate limits
    ```

## 🏃‍♂️ Usage

### Manual Run (Today's Updates)
```bash
uv run src/main.py
```

### Run for Specific Date
```bash
uv run src/main.py --date 2024-02-25
```

## 📦 Deployment Plan

### 1. Environment Variables
Ensure these secrets are set in your GitHub Repository (Settings > Secrets and variables > Actions):
-   `OPENROUTER_API_KEY`: API key for the LLM provider.
-   `GITHUB_TOKEN`: Personal Access Token (Classic) with `public_repo` scope.

### 2. CI/CD Pipeline
The project uses GitHub Actions (`.github/workflows/daily-update.yml`) for continuous delivery.
-   **Trigger**: Scheduled cron job at 23:55 UTC daily.
-   **Process**:
    1.  Checkout code.
    2.  Install `uv` and dependencies.
    3.  Run `src/main.py` to fetch fresh data and generate `site/index.html`.
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
uv run tests/test_flow.py
```

## 🛡️ Architecture

-   **Fetcher (`src/github_client.py`)**:
    -   Uses `tenacity` for exponential backoff retries.
    -   Filters repositories by `pushed_at` timestamp.
    -   Iterates through paginated results until quota is met.
-   **Summarizer (`src/summarizer.py`)**:
    -   Uses LLM to strictly parse CHANGELOGs for specific dates.
    -   Returns `NO_UPDATE` if no entry matches.
-   **Generator (`src/main.py`)**:
    -   Orchestrates the loop.
    -   Generates static HTML with Jinja2.

---
*Powered by OpenRouter and GitHub API.*
