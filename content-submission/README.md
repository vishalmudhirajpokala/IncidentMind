# IncidentMind Content Submission Kit

## Files

- `title-ideas.md` — 20 short, code-grounded title options. Recommended: **How I Designed an Incident Agent Around Hindsight Memory**.
- `article.md` — article draft with code excerpts, links, and a reproducible example.
- `linkedin-post.md` — post under 800 characters plus prepared comments.
- `video-script.md` — timed screen-recording script and five video titles.
- `thumbnail-prompt.md` — 16:9 image-generation prompt, ready for a team photo.
- `asset-checklist.md` — screenshots and publishing tasks still needed.

The checklist also covers tagging Code.in, posting the public article as a Reddit link post, adding the Hindsight first-party comment, and publishing the video to YouTube.

## Verified claims

The repository's end-to-end learning-loop verifier passed **33/33 checks**. That run reports `memory=demo`, `llm=demo`, and `source=local`; it proves the local-memory workflow, not a live Hindsight deployment. The Hindsight HTTP adapter exists in `backend/app/integrations/hindsight_provider.py`, but the root README marks a live external Hindsight endpoint as unverified. The article keeps that distinction explicit.

The run uses a temporary SQLite database and removes it at exit. It does not change the working incident database.

## Replace before publishing

1. Replace `[PROJECT_GITHUB_URL]` in the LinkedIn post with the actual project repository URL. This workspace has no Git remote configured.
2. Replace `[YOUR NAME]` in the video script.
3. Capture and add the screenshots listed in `asset-checklist.md`.
4. After publishing the article, replace `[ARTICLE_URL]` in the first-comment draft.
5. If you verify a live Hindsight bank, update the article's provider-status note with the exact tested mode and behavior. Do not describe the local lexical score as a Hindsight score.

Nothing has been published externally; the LinkedIn and video material is prepared for your review.
