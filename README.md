# TransitionZero · Claude Analytics

A private dashboard of Claude usage across the organisation, hosted on GitHub Pages
at `https://annan-code.github.io/tzcl-analytics/`.

## Files

| File | What it is |
|---|---|
| `index.html` | The dashboard. Static, never changes month to month. |
| `data.enc` | All the figures, encrypted. Useless without the password. |
| `harvest.js` | Collects next month's figures from claude.ai. |

## Why the data is encrypted

This repository is public, because GitHub Pages on a free account cannot publish
from a private repository. The dashboard contains named staff usage and spend, so
the data file is encrypted before it is ever committed.

`data.enc` contains nothing but a salt, an IV and ciphertext. Anyone who downloads
it sees noise. The dashboard asks for a password, derives a key from it in the
browser (PBKDF2-SHA256, 250,000 iterations) and decrypts with AES-256-GCM. The
password is never transmitted and is not stored anywhere.

## Refreshing it each month

1. Sign in to claude.ai as an org admin and open **Analytics → Overview**.
   Let the page finish loading and scroll to the bottom so every panel has rendered.
2. Open the browser console and paste in the contents of `harvest.js`.
   It returns a JSON object containing that month's figures. Everything is fetched;
   nothing is typed in by hand.
3. Hand that JSON to Claude and ask it to refresh the dashboard. It rebuilds
   `data.enc` and pushes it here.
4. GitHub Pages rebuilds within a couple of minutes. The URL does not change,
   so there is nothing to send anyone.

## Where the numbers come from

Spend figures come from the internal analytics JSON API. The remaining panels are
read from the rendered analytics pages, because the full analytics API is only
available on Enterprise plans.

Two limitations worth knowing:

- **Per-engineer Claude Code detail is unavailable** until the Claude Code GitHub
  app is confirmed on the TransitionZero repositories. Until then the per-user PR
  and lines-of-code panels show "Data processing".
- **The time-saved figure is Anthropic's own model**, driven mostly by an
  assumption of 150 minutes saved per pull request. Treat it as an order of
  magnitude rather than a measurement.
