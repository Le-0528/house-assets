import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="우리 집 재산관리대장",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:      #F7F6F2;
    --surface: #FFFFFF;
    --border:  #E8E4DC;
    --accent:  #2D6A4F;
    --accent2: #52B788;
    --warn:    #E07A5F;
    --warn-bg: #FDF0ED;
    --text:    #1A1A1A;
    --muted:   #8A8680;
    --badge:   #F0EDE6;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text);
}

.main-header {
    background: var(--surface);
    border-bottom: 3px solid var(--accent);
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.4rem;
    border-radius: 12px;
    display: flex; align-items: center; gap: 1rem;
}
.main-header h1 { font-size: 1.6rem; font-weight: 700; color: var(--accent); margin: 0; }
.main-header p  { font-size: 0.8rem; color: var(--muted); margin: 0.15rem 0 0; }

.stat-row { display: flex; gap: 0.9rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 0.9rem 1.2rem; flex: 1; min-width: 120px;
}
.stat-card .label { font-size: 0.72rem; color: var(--muted); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; }
.stat-card .value { font-size: 1.4rem; font-weight: 700; color: var(--accent);
    font-family: 'DM Mono', monospace; }
.stat-card .sub   { font-size: 0.7rem; color: var(--muted); margin-top: 1px; }

.alert-box {
    background: var(--warn-bg); border: 1.5px solid var(--warn);
    border-radius: 10px; padding: 1rem 1.4rem; margin-bottom: 1.2rem;
}
.alert-box h4 { color: var(--warn); margin: 0 0 0.5rem; font-size: 0.92rem; }
.alert-item   { font-size: 0.82rem; padding: 0.22rem 0; display: flex; align-items: center; gap: 0.5rem; }
.alert-item .days { font-family: 'DM Mono', monospace; font-weight: 600; color: var(--warn); }

.section-title {
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.35rem; margin: 1.1rem 0 0.7rem;
}

section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }

.stButton > button {
    background: var(--accent) !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 500 !important; transition: opacity 0.15s;
}
.stButton > button:hover { opacity: 0.82; }
</style>
""", unsafe_allow_html=True)

# ── 상수 ─────────────────────────────────────────────────────
EXCEL_PATH = "assets.xlsx"
COLUMNS    = ["물품명", "장소", "금액", "구매날짜", "카테고리", "폐기예정일"]
CATEGORIES = ["가전제품", "가구", "주방용품", "생활용품", "의류/침구", "IT기기", "차량/이동수단", "기타"]
PLACES     = ["안방", "거실", "주방", "욕실", "서재", "아이방", "베란다", "창고", "기타"]

# ── 데이터 로직 ──────────────────────────────────────────────
def load_data():
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        df["구매날짜"]   = pd.to_datetime(df["구매날짜"],   errors="coerce")
        df["폐기예정일"] = pd.to_datetime(df["폐기예정일"], errors="coerce")
    else:
        df = pd.DataFrame(columns=COLUMNS)
    return df

def save_data(df):
    df.to_excel(EXCEL_PATH, index=False)

def calc_d_plus(purchase_date):
    if pd.isna(purchase_date): return "-"
    delta = (date.today() - purchase_date.date()).days
    return f"D+{delta:03d}"

def calc_d_minus(disposal_date):
    if pd.isna(disposal_date): return "-"
    delta = (disposal_date.date() - date.today()).days
    return f"D-{delta:03d}" if delta >= 0 else f"⚠️ {abs(delta)}일 초과"

def fmt_price(v):
    try:    return f"₩{int(v):,}"
    except: return "-"

# ── 데이터 로드 ──────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load_data()
df = st.session_state.df

# ── 헤더 ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <div style="font-size:2rem">🏠</div>
  <div>
    <h1>우리 집 재산관리대장</h1>
    <p>오늘: {date.today().strftime('%Y년 %m월 %d일')} &nbsp;·&nbsp; 총 {len(df)}개 물품 등록</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 교체 알림 ─────────────────────────────────────────────────
if not df.empty and df["폐기예정일"].notna().any():
    threshold = pd.Timestamp(date.today()) + pd.Timedelta(days=30)
    alerts = df[df["폐기예정일"].notna() & (df["폐기예정일"] <= threshold)].sort_values("폐기예정일")
    if not alerts.empty:
        items_html = "".join(
            f'<div class="alert-item">🔔 <b>{r["물품명"]}</b> ({r["장소"]}) '
            f'<span class="days">{calc_d_minus(r["폐기예정일"])}</span>'
            f' · {r["폐기예정일"].strftime("%Y-%m-%d")}</div>'
            for _, r in alerts.iterrows()
        )
        st.markdown(f"""
        <div class="alert-box">
            <h4>🚨 교체 알림 — 30일 이내 폐기 예정 물품 {len(alerts)}건</h4>
            {items_html}
        </div>""", unsafe_allow_html=True)

# ── 통계 카드 ─────────────────────────────────────────────────
if not df.empty:
    total_val  = df["금액"].fillna(0).sum()
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="label">총 물품</div>
            <div class="value">{len(df)}</div>
            <div class="sub">개 등록됨</div>
        </div>
        <div class="stat-card">
            <div class="label">총 자산가치</div>
            <div class="value" style="font-size:1.15rem">{fmt_price(total_val)}</div>
            <div class="sub">등록 물품 합계</div>
        </div>
        <div class="stat-card">
            <div class="label">카테고리</div>
            <div class="value">{df["카테고리"].nunique()}</div>
            <div class="sub">종류</div>
        </div>
        <div class="stat-card">
            <div class="label">등록 장소</div>
            <div class="value">{df["장소"].nunique()}</div>
            <div class="sub">구역</div>
        </div>
    </div>""", unsafe_allow_html=True)

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ➕ 물품 관리")
    mode = st.radio("모드", ["새 물품 추가", "기존 물품 수정"], horizontal=True)

    if mode == "기존 물품 수정" and not df.empty:
        edit_idx = st.selectbox("수정할 물품", df.index, format_func=lambda i: df.loc[i, "물품명"])
        r = df.loc[edit_idx]
        d_name  = r["물품명"]
        d_place = r["장소"]  if r["장소"] in PLACES else PLACES[0]
        d_price = int(r["금액"]) if pd.notna(r["금액"]) else 0
        d_buy   = r["구매날짜"].date()   if pd.notna(r["구매날짜"])   else date.today()
        d_cat   = r["카테고리"] if r["카테고리"] in CATEGORIES else CATEGORIES[0]
        d_dis   = r["폐기예정일"].date() if pd.notna(r["폐기예정일"]) else date.today() + timedelta(days=365)
    else:
        edit_idx = None
        d_name, d_place, d_price = "", PLACES[0], 0
        d_buy  = date.today()
        d_cat  = CATEGORIES[0]
        d_dis  = date.today() + timedelta(days=365 * 3)

    with st.form("asset_form", clear_on_submit=(mode == "새 물품 추가")):
        name     = st.text_input("물품명 *",     value=d_name,  placeholder="예: LG 세탁기")
        place    = st.selectbox("장소 *",         PLACES,        index=PLACES.index(d_place))
        price    = st.number_input("금액 (원)",   min_value=0,   value=d_price, step=1000, format="%d")
        buy_date = st.date_input("구매날짜",      value=d_buy)
        category = st.selectbox("카테고리",       CATEGORIES,    index=CATEGORIES.index(d_cat))
        dis_date = st.date_input("폐기예정일",    value=d_dis)
        submitted = st.form_submit_button("💾 저장하기", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("물품명을 입력해주세요.")
            else:
                row = dict(
                    물품명=name.strip(), 장소=place, 금액=price,
                    구매날짜=pd.Timestamp(buy_date), 카테고리=category,
                    폐기예정일=pd.Timestamp(dis_date),
                )
                if mode == "기존 물품 수정" and edit_idx is not None:
                    for k, v in row.items():
                        st.session_state.df.loc[edit_idx, k] = v
                    st.success("✅ 수정 완료!")
                else:
                    st.session_state.df = pd.concat(
                        [st.session_state.df, pd.DataFrame([row])], ignore_index=True)
                    st.success(f"✅ '{name}' 등록 완료!")
                save_data(st.session_state.df)
                st.rerun()

    if not df.empty:
        st.markdown("---")
        st.markdown("### 🗑️ 물품 삭제")
        del_idx = st.selectbox("삭제할 물품", df.index,
                               format_func=lambda i: df.loc[i, "물품명"], key="del")
        if st.button("삭제하기", use_container_width=True):
            nm = st.session_state.df.loc[del_idx, "물품명"]
            st.session_state.df = st.session_state.df.drop(index=del_idx).reset_index(drop=True)
            save_data(st.session_state.df)
            st.success(f"🗑️ '{nm}' 삭제 완료!")
            st.rerun()

# ── 메인: 검색 & 필터 ─────────────────────────────────────────
df = st.session_state.df
st.markdown('<div class="section-title">검색 및 필터</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    search = st.text_input("🔍 물품 검색", placeholder="물품명 또는 카테고리...", label_visibility="collapsed")
with c2:
    place_f = st.multiselect("장소 필터",     PLACES,      placeholder="전체 장소")
with c3:
    cat_f   = st.multiselect("카테고리 필터", CATEGORIES,  placeholder="전체 카테고리")

view_df = df.copy()
if search:
    m = (view_df["물품명"].astype(str).str.contains(search, case=False, na=False) |
         view_df["카테고리"].astype(str).str.contains(search, case=False, na=False))
    view_df = view_df[m]
if place_f: view_df = view_df[view_df["장소"].isin(place_f)]
if cat_f:   view_df = view_df[view_df["카테고리"].isin(cat_f)]

# ── 목록 테이블 ───────────────────────────────────────────────
st.markdown('<div class="section-title">물품 목록</div>', unsafe_allow_html=True)

if view_df.empty:
    st.info("등록된 물품이 없습니다. 사이드바에서 물품을 추가해보세요! 😊")
else:
    disp = view_df.copy()
    disp["사용기간"]   = disp["구매날짜"].apply(calc_d_plus)
    disp["남은수명"]   = disp["폐기예정일"].apply(calc_d_minus)
    disp["금액"]       = disp["금액"].apply(fmt_price)
    disp["구매날짜"]   = disp["구매날짜"].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "-")
    disp["폐기예정일"] = disp["폐기예정일"].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "-")

    show = ["물품명","장소","카테고리","금액","구매날짜","사용기간","폐기예정일","남은수명"]
    st.dataframe(
        disp[show].reset_index(drop=True),
        use_container_width=True, height=420,
        column_config={
            "물품명":    st.column_config.TextColumn("📦 물품명",   width="medium"),
            "장소":      st.column_config.TextColumn("📍 장소",     width="small"),
            "카테고리":  st.column_config.TextColumn("🏷️ 카테고리", width="medium"),
            "금액":      st.column_config.TextColumn("💰 금액",     width="medium"),
            "구매날짜":  st.column_config.TextColumn("🗓️ 구매날짜", width="medium"),
            "사용기간":  st.column_config.TextColumn("⏱️ 사용기간", width="small"),
            "폐기예정일":st.column_config.TextColumn("📅 폐기예정일",width="medium"),
            "남은수명":  st.column_config.TextColumn("⌛ 남은수명", width="small"),
        }
    )
    st.caption(f"총 {len(view_df)}개 물품 표시 중")

# ── 장소별 요약 ───────────────────────────────────────────────
if not df.empty:
    st.markdown('<div class="section-title">장소별 요약</div>', unsafe_allow_html=True)
    with st.expander("📊 장소별 자산 현황 펼치기"):
        summary = (
            df.groupby("장소")
            .agg(물품수=("물품명","count"), 총금액=("금액","sum"))
            .reset_index().sort_values("총금액", ascending=False)
        )
        summary["총금액"] = summary["총금액"].apply(fmt_price)
        st.dataframe(summary, use_container_width=True, hide_index=True)
