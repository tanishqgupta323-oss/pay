import html
import re
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

SHEET_ID = "1wJDOWDZL_7l-N-9yt5PhHJtVWsgF_mfbmlPohgr-Jyw"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
REFRESH_SECONDS = 3  # how often every open page checks the sheet (shared across all students)

st.set_page_config(
    page_title="Live Payments",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #070b1a; }
    header, footer, [data-testid="stSidebar"], [data-testid="collapsedControl"],
    [data-testid="stToolbar"] { display: none !important; }
    .block-container { padding: 0.5rem 0.5rem 2rem !important; max-width: 100% !important; }
    [data-testid="stCaptionContainer"] { color: #8a93b8; text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Find the header row, split side-by-side sections (A/B) and stack them."""
    raw = raw.fillna("").astype(str).apply(lambda c: c.str.strip())
    if raw.empty:
        return raw

    # header row = first row that mentions "payment" (else first row with 3+ filled cells)
    hdr = None
    for i in range(min(len(raw), 30)):
        vals = [v.lower() for v in raw.iloc[i]]
        if sum(v != "" for v in vals) >= 3 and any("payment" in v or "amount" in v for v in vals):
            hdr = i
            break
    if hdr is None:
        for i in range(min(len(raw), 30)):
            if sum(v != "" for v in raw.iloc[i]) >= 3:
                hdr = i
                break
    hdr = hdr or 0

    headers = raw.iloc[hdr].tolist()
    data = raw.iloc[hdr + 1 :]
    data = data.reset_index(drop=True)
    # drop only the blank rows at the very end; blank rows in between stay as visible gaps
    nonblank = data.apply(lambda r: any(v != "" for v in r), axis=1)
    last = int(nonblank[nonblank].index.max()) if nonblank.any() else -1
    data = data.iloc[: last + 1].reset_index(drop=True)

    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    def letter(n: int) -> str:  # 0 -> A, 25 -> Z, 26 -> AA
        s, n = "", n + 1
        while n:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    def uniq(cols):
        seen, out = {}, []
        for c in cols:
            n = seen.get(c, 0)
            seen[c] = n + 1
            out.append(c if n == 0 else f"{c} {n + 1}")
        return out

    # keep EVERY column that has a header or any data, so new columns show up automatically
    def used(j: int) -> bool:
        return bool(headers[j]) or bool((data.iloc[:, j] != "").any())

    used_cols = [j for j in range(len(headers)) if used(j)]
    if not used_cols:
        return data
    # everything from the first to the last used column, so a column you leave empty stays a gap
    keep = list(range(used_cols[0], used_cols[-1] + 1))
    df = data.iloc[:, keep].copy()
    df.columns = uniq([headers[j] or f"Column {letter(j)}" for j in keep])

    # a repeated first header (S. No. ... S. No.) marks where a new side-by-side section starts
    first = norm(headers[keep[0]])
    # rows above the header row (e.g. a heading you type at the top of the sheet)
    df.attrs["titles"] = [
        " ".join(v for v in raw.iloc[i] if v) for i in range(hdr) if any(v for v in raw.iloc[i])
    ]
    df.attrs["labels"] =[headers[j] or f"Column {letter(j)}" for j in keep]  # as in the sheet
    gaps = [p for p, j in enumerate(keep) if not used(j)]
    df.attrs["gaps"] = gaps
    df.attrs["breaks"] = [
        p
        for p, j in enumerate(keep)
        if p > 0 and headers[j] and norm(headers[j]) == first and (p - 1) not in gaps
    ]
    return df


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_raw() -> pd.DataFrame:
    """One download of the sheet is shared by every student who has the page open."""
    return pd.read_csv(
        f"{CSV_URL}&t={int(time.time())}", header=None, dtype=str, keep_default_na=False
    )


def load_data() -> pd.DataFrame:
    return tidy(fetch_raw())


PAGE = """
<style>
  * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
  body { margin: 0; background: transparent; color: #e8ecff; overflow-x: auto; }
  .wrap { position: relative; padding: 18px 8px 40px; }
  .orb { position: fixed; border-radius: 50%; filter: blur(70px); opacity: .35; z-index: 0;
         animation: drift 14s ease-in-out infinite alternate; pointer-events: none; }
  .o1 { width: 280px; height: 280px; background: #00e5ff; top: -60px; left: -40px; }
  .o2 { width: 320px; height: 320px; background: #b400ff; bottom: -80px; right: -60px; animation-delay: -6s; }
  @keyframes drift { to { transform: translate(60px, 40px) scale(1.15); } }
  .titles { position: relative; z-index: 1; text-align: center; margin-bottom: 18px; }
  .titles .t { font-weight: 800; letter-spacing: 1px; display: inline-block;
               background: linear-gradient(90deg, #00e5ff, #b400ff, #39ff88, #00e5ff);
               background-size: 300% 100%; -webkit-background-clip: text; background-clip: text;
               color: transparent; animation: shine 6s linear infinite, float 4s ease-in-out infinite; }
  .titles .t0 { font-size: 34px; } .titles .t1 { font-size: 18px; opacity: .9; }
  @keyframes shine { to { background-position: 300% 0; } }
  .stats { position: relative; z-index: 1; display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
  .chip { padding: 10px 18px; border-radius: 14px; background: rgba(255,255,255,.06);
          border: 1px solid rgba(0,229,255,.35); box-shadow: 0 0 18px rgba(0,229,255,.15); }
  .chip b { color: #00e5ff; font-size: 20px; margin-left: 6px; }
  .grid { position: relative; z-index: 1; display: grid; gap: 10px;
          grid-template-columns: COLS; }
  .head { padding: 10px 14px; border-radius: 12px; font-weight: 700; letter-spacing: .5px;
          text-transform: uppercase; font-size: 12px; color: #00e5ff;
          background: rgba(0,229,255,.08); border: 1px solid rgba(0,229,255,.4); text-align: center; }
  .row { display: contents; }
  .cell { padding: 14px; border-radius: 14px; text-align: center; word-break: break-word;
          background: rgba(255,255,255,.07); backdrop-filter: blur(6px);
          border: 1px solid rgba(255,255,255,.12);
          animation: float 4s ease-in-out infinite; animation-delay: var(--d); }
  @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
  .row.new .cell { animation: pop .8s cubic-bezier(.2,1.4,.4,1) both, float 4s ease-in-out .8s infinite,
                              glow 1.6s ease-out 3; border-color: #39ff88; }
  @keyframes pop { from { opacity: 0; transform: translateY(40px) scale(.7); } to { opacity: 1; transform: none; } }
  @keyframes glow { 0% { box-shadow: 0 0 0 rgba(57,255,136,0); } 40% { box-shadow: 0 0 26px rgba(57,255,136,.9); }
                    100% { box-shadow: 0 0 0 rgba(57,255,136,0); } }
  .cell.edit { border-color: #ffb300; animation: flash 1.2s ease-out 3, float 4s ease-in-out infinite;
               animation-delay: 0s, var(--d); }
  @keyframes flash { 0% { background: rgba(255,179,0,.7); transform: scale(1.08); }
                     100% { background: rgba(255,255,255,.07); transform: scale(1); } }
  .cell.blank { padding: 4px; background: none; border-color: transparent;
                backdrop-filter: none; animation: none; box-shadow: none; }
  .empty { position: relative; z-index: 1; text-align: center; padding: 60px; opacity: .7; }
  :root { --w: 110px; --g: 34px; }
  @media (max-width: 700px) {
    :root { --w: 66px; --g: 14px; }
    .wrap { padding: 8px 4px 24px; }
    .grid { gap: 6px; }
    .cell { padding: 8px 3px; font-size: 12px; border-radius: 10px; backdrop-filter: none; }
    .head { padding: 6px 2px; font-size: 9px; border-radius: 8px; }
    .titles .t0 { font-size: 22px; } .titles .t1 { font-size: 14px; }
    .orb { filter: blur(40px); opacity: .25; }
  }
</style>
<div class="wrap">
  <div class="orb o1"></div><div class="orb o2"></div>
  <div class="titles">TITLES</div>
  <div class="grid">HEADERS ROWS</div>
</div>
"""


def build_html(df: pd.DataFrame, marks: dict) -> str:
    cols = list(df.columns)
    breaks = set(df.attrs.get("breaks", []))  # gap before each new side-by-side section
    labels = df.attrs.get("labels") or cols
    if len(labels) != len(cols):
        labels = cols

    titles_html = "".join(
        f'<div class="t t{min(k, 1)}">{html.escape(t)}</div><br>'
        for k, t in enumerate(df.attrs.get("titles", []))
    )

    gaps = set(df.attrs.get("gaps", []))  # columns you left empty in the sheet

    tracks, headers = [], ""
    for j, c in enumerate(cols):
        if j in breaks:
            tracks.append("var(--g)")
            headers += "<div></div>"
        if j in gaps:
            tracks.append("var(--g)")
            headers += "<div></div>"
            continue
        tracks.append("minmax(var(--w), 1fr)")
        headers += f'<div class="head">{html.escape(str(labels[j]))}</div>'

    rows_html = []
    for i, row in enumerate(df.values.tolist()):
        mark = marks.get(i)
        row_cls = "row new" if mark == "new" else "row"
        cells = []
        blank_row = all(v == "" for v in row)  # a row you left empty stays a gap
        for j, val in enumerate(row):
            if j in breaks:
                cells.append("<div></div>")
            if j in gaps:
                cells.append("<div></div>")
                continue
            cell_cls = "cell edit" if isinstance(mark, list) and j in mark else "cell"
            if blank_row:
                cell_cls = "cell blank"
            delay = f"-{((i * 7 + j * 3) % 40) / 10:.1f}s"
            cells.append(f'<div class="{cell_cls}" style="--d:{delay}">{html.escape(val)}</div>')
        rows_html.append(f'<div class="{row_cls}">{"".join(cells)}</div>')

    body = headers + "".join(rows_html)
    if df.empty:
        body = '<div class="empty">Sheet khali hai. Kuch rows add karo.</div>'

    return (
        PAGE.replace("COLS", " ".join(tracks) or "1fr")
        .replace("TITLES", titles_html)
        .replace("HEADERS ROWS", body)
    )


def compute_marks(df: pd.DataFrame) -> dict:
    cur = df.values.tolist()
    cols = list(df.columns)
    prev = st.session_state.get("prev")
    prev_cols = st.session_state.get("prev_cols")

    if prev is None:
        st.session_state.marks = {}
    elif prev_cols != cols:
        # columns added/renamed in the sheet: flash the new column's cells
        new_idx = [j for j, c in enumerate(cols) if c not in prev_cols]
        st.session_state.marks = {i: new_idx for i in range(len(cur))} if new_idx else {}
    elif cur != prev:
        marks = {}
        for i, row in enumerate(cur):
            if i >= len(prev):
                marks[i] = "new"
            else:
                changed = [j for j, (a, b) in enumerate(zip(row, prev[i])) if a != b]
                if changed:
                    marks[i] = changed
        st.session_state.marks = marks

    st.session_state.prev = cur
    st.session_state.prev_cols = cols
    return st.session_state.get("marks", {})


def live_view():
    try:
        df = load_data()
        st.session_state.last_df = df
        st.session_state.pop("error", None)
    except Exception as e:  # keep showing the last good data
        st.session_state.error = str(e)
        df = st.session_state.get("last_df")

    if st.session_state.get("error"):
        st.warning(
            "Sheet abhi load nahi ho rahi. Sheet ka Share > 'Anyone with the link' > Viewer "
            "hona chahiye. Thodi der baad apne aap dobara try hoga."
        )
    if df is None:
        return

    marks = compute_marks(df)
    # tall enough for every row, so the page itself scrolls (no scroll-inside-scroll on phones)
    height = 170 + 66 * (len(df) + 1) + 44 * len(df.attrs.get("titles", []))
    components.html(build_html(df, marks), height=height, scrolling=True)
    st.caption(f"Live  |  updated {time.strftime('%H:%M:%S')}  |  green = new, orange = edited")


st.fragment(run_every=REFRESH_SECONDS)(live_view)()