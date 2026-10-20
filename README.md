# Live Animated Payments Board

Single-file static site (HTML + CSS + JS) that reads a public Google Sheet every 3 seconds and shows a neon live board.

## Files

| File        | Purpose                                      |
|-------------|----------------------------------------------|
| `index.html`| Complete site (inline CSS + JS)              |
| `worker.js` | Optional Cloudflare Worker (CORS + 3s cache) |

## Quick start – Cloudflare Pages (Direct Upload)

1. Open [Cloudflare Dashboard](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Upload assets**.
2. Project name: e.g. `payments-board` (lowercase, hyphens ok).
3. Drag the **folder that contains `index.html`** (or zip it first) into the upload area.  
   Make sure `index.html` is at the **root** of the upload, not inside an extra sub-folder.
4. Click **Deploy site**.
5. Open the `*.pages.dev` URL on your phone.

You can re-upload the same folder later to update the site.

## CORS / Worker (recommended)

Browsers usually block direct `fetch` of the Google Sheets export URL (no `Access-Control-Allow-Origin`).  
If the board shows “Cannot load sheet” or the console has a CORS error:

1. Deploy the Worker (steps below).
2. Open `index.html` and set the constant at the top:

```js
const WORKER_URL = "https://YOUR-WORKER-NAME.YOUR-SUBDOMAIN.workers.dev";
```

3. Re-upload `index.html` to Pages.

### Deploy the Worker from the dashboard

1. Dashboard → **Workers & Pages** → **Create** → **Worker**.
2. Choose a name (e.g. `payments-sheet`) → **Deploy**.
3. Click **Edit code**.
4. Delete the default code and paste the entire contents of `worker.js`.
5. **Save and Deploy**.
6. Copy the `*.workers.dev` URL and put it into `WORKER_URL` in `index.html`.

The Worker caches the CSV for 3 seconds so many phones do not hit Google on every poll.

## How to detect CORS failure

Open the site → DevTools (or remote debug on phone) → Console.  
If you see:

```
Access to fetch at 'https://docs.google.com/...' from origin 'https://....pages.dev'
has been blocked by CORS policy
```

→ switch to the Worker URL.

## Test checklist

| Action | Expected |
|--------|----------|
| Edit a PAYMENT cell (e.g. blank → 750) | That cell flashes orange a few times |
| Add a new student row | New row appears with green glow |
| Add a brand-new column anywhere | New column appears; its cells flash once (purple-ish) |
| Leave a middle column completely empty | Narrow visual gap remains (columns do not stick together) |
| Add a title row above the header (e.g. “FEE SHEET”) | Big neon gradient text appears above the board |
| TOTAL / sum row at bottom | Shows as a normal data row |
| Put phone in airplane mode briefly | Footer shows “Reconnecting…”, last good data stays |
| Rotate phone / 360 px width | Horizontal swipe works, columns stay side-by-side |

## Notes

- Section A and Section B stay **side-by-side** (second “S. No.” creates a small gap).
- No settings, no buttons, no third-party scripts/fonts.
- Polls every 3 s only when the tab is visible.
- Respects `prefers-reduced-motion`.
