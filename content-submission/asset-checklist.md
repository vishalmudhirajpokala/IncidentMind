# Article Assets and Publish Checklist

## Screenshots to capture

- `assets/01-command-center.png` — `/dashboard`, showing the incident list and memory-related summary. Caption: “The command center puts incidents, investigation history, and retained experience in one operational view.”
- `assets/02-investigation.png` — `/incidents/INC-011` after investigation, showing current signals, recalled evidence, and recommendation. Caption: “The recommendation is presented with the evidence that informed it.”
- `assets/03-memory-off-on.png` — the same incident's memory-off and memory-on comparison, with provider mode visible. Caption: “The control path withholds memory while keeping the incident and analyst constant.”
- `assets/04-learning-loop.png` — the output from `python scripts/verify_learning_loop.py`, cropped to the memory-off/on result and the final check count. Caption: “The repeatable local-provider verification reports what it actually recalled.”

Keep IDs and operational details visible only if they are safe to publish. Use the seeded disposable data, not real customer or production information. Do not crop away the `demo`/`local` provider labels.

## Before publishing

- Confirm the article is between 800 and 1,500 words after edits.
- Insert the screenshots above and keep their captions accurate to the provider mode shown.
- Replace `[PROJECT_GITHUB_URL]`, `[YOUR NAME]`, and `[ARTICLE_URL]` in the relevant files.
- If describing external Hindsight as live, first verify the configured Hindsight endpoint and capture its provider status; otherwise keep the current local-provider caveat.
- Publish the article publicly, then publish the LinkedIn post with the project URL and put the article URL in the first comment.
- Add the Hindsight repository link in a separate LinkedIn comment.
- Tag Code.in on LinkedIn and the article.
- Share the public article as a link post on one relevant subreddit: `r/llmdevs`, `r/sideproject`, `r/aiagents`, or `r/aimemory`.
- Record the video, generate the thumbnail using the attached team photo, and publish it publicly on YouTube.
