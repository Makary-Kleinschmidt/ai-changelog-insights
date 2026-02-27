# Changelog - AI Changelog Insights

All notable changes to this project will be documented in this file.

## [1.2.3] - 2026-02-27

### Changed
- **Model Hierarchy**: Restored `gemini-3-flash-preview` as the primary model and `gemini-2.5-flash` as the first fallback, following user preference for higher quality models.
- **Fallback Logic**: Configured fallback chain to strictly follow quality tiering: 3.0 -> 2.5 -> 2.0 -> 1.5, ensuring lower-tier models are only used when higher tiers are genuinely exhausted.

## [1.2.2] - 2026-02-27

### Fixed
- **Empty Content Fallback**: Updated `GEMINI_FALLBACK_MODELS` in `config.py` to include a robust list of valid models (`gemini-2.0-flash`, `gemini-2.0-flash-lite-preview-02-05`, `gemini-1.5-flash`, `gemini-1.5-flash-8b`, `gemini-1.5-pro`) to prevent empty content generation when primary model quota is exhausted.
- **Model Configuration**: Removed invalid/deprecated model names (`gemini-2.5-flash`, `gemini-3-flash-preview`) from fallback list to avoid unnecessary API errors.

## [1.2.1] - 2026-02-27

### Fixed
- **Empty Content Issue**: Switched primary model to `gemini-2.0-flash` due to `gemini-3-flash-preview` quota exhaustion.
- **UI Visibility**: Fixed an issue where code snippets were not fully visible inside accordions by adding dynamic height adjustment logic.
- **Copy Button**: Fixed the "Copy" button functionality to correctly copy code without including the button text and improved feedback animation.

## [1.2.0] - 2026-02-26

### Fixed
- **JSON Truncation**: Increased `MAX_OUTPUT_TOKENS` to 16,000 and added truncated-JSON repair that closes open strings/arrays/objects when LLM output is cut off mid-generation.
- **Duplicate Fallback Model**: Removed `gemini-3-flash-preview` from `GEMINI_FALLBACK_MODELS` — it was identical to the primary model, causing wasted retry cycles.
- **504 Deadline Exceeded**: Now treated as a retryable error (alongside 503 and 429) instead of causing immediate model switch.
- **Server Retry Delay**: The system now extracts and respects the `retryDelay` suggested in API error responses instead of always using a fixed 30s wait.

### Changed
- **MAX_RETRIES**: Reduced from 3 to 2 per model — with the duplicate removed, fewer retries are needed.
- **Documentation**: Rewrote `ARCHITECTURE.md` (was still referencing Wikipedia/scraper pattern). Updated `README.md` with correct commands and feature descriptions.

## [1.1.0] - 2026-02-26

### Added
- **Gemini 3 Flash Preview Integration**: Switched LLM provider from OpenRouter to Google Gemini API using the official `google-genai` SDK.
- **Model Fallback System**: Automated sequence to try `gemini-3-flash-preview` -> `gemini-2.5-flash` -> `gemini-2.0-flash` if preferred models are unavailable.
- **503 Retry Mechanism**: Implemented automatic linear backoff (30s delay, 3 retries) for "Service Unavailable" and "Rate Limit" errors.
- **3-Level Try It Out**: Output now includes separate Beginner, Intermediate, and Advanced implementation examples in collapsible sections.
- **Ecosystem Summary Toggles**: The global ecosystem analysis is now collapsed by default for a cleaner dashboard view.

### Changed
- **What's New Section**: Transformed from a single paragraph into a factual bulletted list.
- **Hyperlink Rendering**: Fixed an issue where Markdown links in summaries were not clickable; they are now properly parsed to HTML `<a>` tags.
- **Prompt Engineering**: Refactored `GLOBAL_SUMMARY_PROMPT` for progressive, non-labeled analysis (Beginner -> Advanced flow).
- **Token Limits**: Increased `max_output_tokens` to 4000 to prevent JSON truncation in complex responses.
- **Rate Limiting**: Added 12s sleep between calls to adhere to 5 RPM free tier limits.

### Fixed
- Robust JSON extraction using regex to handle non-JSON preamble/postamble from LLM responses.
- Fixed corrupted line markers in `README.md`.

## [1.0.0] - 2026-02-25
- Initial release with OpenRouter integration and GitHub aggregation.
