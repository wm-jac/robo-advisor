"""
app.py  —  BMD5302 Robo-Advisor  (Streamlit, bilingual EN/ZH)
Run with:  streamlit run app.py
"""

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import (
    annualise_stats,
    compute_returns,
    individual_fund_stats,
    load_all_funds,
    normalise_prices,
)
from src.optimizer import find_optimal_portfolio, sensitivity_analysis
from src.portfolio import compute_efficient_frontier, compute_gmvp, portfolio_stats
from src.risk_assessment import QUESTIONS, calculate_utility, describe_profile, get_score_range, score_to_A
from src.translations import PROFILE_KEY_MAP, TRANSLATIONS

DATA_DIR = Path(__file__).resolve().parent / "data"

# ──────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BMD5302 Robo-Advisor",
    page_icon="📈",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────
# Language helpers
# ──────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"


def t(key: str) -> str:
    """Return the UI string for the current language, falling back to English."""
    lang = st.session_state.get("lang", "en")
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return tr.get(key, TRANSLATIONS["en"].get(key, key))


def translate_profile(profile: dict) -> dict:
    """Return a copy of the profile dict with label/description in the current language."""
    key = PROFILE_KEY_MAP.get(profile["label"], "moderate")
    return {
        **profile,
        "label": t(f"profile_{key}_label"),
        "description": t(f"profile_{key}_desc"),
    }


# Internal freq values that the backend always expects
_FREQ_EN = ["Daily", "Weekly", "Monthly"]

# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Language toggle ──
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button(
            "EN",
            use_container_width=True,
            type="primary" if st.session_state["lang"] == "en" else "secondary",
        ):
            st.session_state["lang"] = "en"
            st.rerun()
    with lang_col2:
        if st.button(
            "中",
            use_container_width=True,
            type="primary" if st.session_state["lang"] == "zh" else "secondary",
        ):
            st.session_state["lang"] = "zh"
            st.rerun()

    st.title(t("title"))
    st.markdown(f"**{t('subtitle')}**")
    st.divider()

    uploaded_files = st.file_uploader(
        t("upload_label"),
        type=["csv"],
        accept_multiple_files=True,
        help=t("upload_help"),
    )

    # Frequency selectbox — display translated options, store index for backend mapping
    freq_options_display = t("freq_options")
    saved_freq_idx = st.session_state.get("freq_idx", 0)
    freq_display = st.selectbox(t("freq_label"), options=freq_options_display, index=saved_freq_idx)
    freq_idx = freq_options_display.index(freq_display)
    st.session_state["freq_idx"] = freq_idx
    freq = _FREQ_EN[freq_idx]  # always pass English key to backend

    allow_short = st.toggle(t("allow_short"), value=False)

    st.divider()
    st.caption(t("semester"))

# ──────────────────────────────────────────────────────────────
# Data loading (cached)
# ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_data(file_bytes_list: list[bytes], file_names: list[str], freq: str):
    """Cache-friendly wrapper: receives raw bytes so Streamlit can hash them."""
    file_objs = [io.BytesIO(b) for b in file_bytes_list]
    for fobj, name in zip(file_objs, file_names):
        fobj.name = name
    prices = load_all_funds(file_objs, file_names)
    returns = compute_returns(prices, method="log")
    mu, Sigma = annualise_stats(returns, freq=freq)
    return prices, returns, mu, Sigma


def _default_data_files() -> list[Path]:
    return sorted(path for path in DATA_DIR.glob("*.csv") if path.is_file())


def _humanise_fund_label(name: str) -> str:
    label = Path(str(name)).stem
    parts = label.split("_", 1)
    if len(parts) == 2 and any(char.isdigit() for char in parts[0]):
        label = parts[1]
    label = label.replace("_", " ").replace("-", " ")
    return " ".join(label.split())


def _humanise_fund_labels(names: list[str]) -> list[str]:
    labels = [_humanise_fund_label(name) for name in names]
    counts = {}
    unique_labels = []
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
        unique_labels.append(label if counts[label] == 1 else f"{label} ({counts[label]})")
    return unique_labels


def get_data():
    if uploaded_files:
        file_bytes = [f.read() for f in uploaded_files]
        for f in uploaded_files:
            f.seek(0)
        file_names = _humanise_fund_labels([Path(f.name).stem for f in uploaded_files])
    else:
        data_files = _default_data_files()
        if not data_files:
            return None, None, None, None
        file_bytes = [path.read_bytes() for path in data_files]
        file_names = _humanise_fund_labels([path.stem for path in data_files])

    try:
        prices, returns, mu, Sigma = _load_data(file_bytes, file_names, freq)
        return prices, returns, mu, Sigma
    except Exception as e:
        st.error(t("tab1_error").format(e=e))
        return None, None, None, None


# ──────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([t("tab1"), t("tab2"), t("tab3"), t("tab4")])

# ══════════════════════════════════════════════════════════════
# TAB 1 — Data & Funds
# ══════════════════════════════════════════════════════════════
with tab1:
    st.header(t("tab1_header"))

    if not uploaded_files:
        default_files = _default_data_files()
        if default_files:
            st.info(t("tab1_using_default").format(n=len(default_files)))
        else:
            st.info(t("tab1_upload_info"))
            st.markdown(t("tab1_how_to"))
            st.markdown(t("tab1_steps"))
            st.stop()

    prices, returns, mu, Sigma = get_data()
    if prices is None:
        st.stop()

    data_source = t("tab1_source_upload") if uploaded_files else t("tab1_source_local")
    st.success(
        t("tab1_loaded").format(
            n=len(prices.columns),
            source=data_source,
            start=prices.index[0].date(),
            end=prices.index[-1].date(),
            obs=len(prices),
        )
    )

    # Normalised price chart
    st.subheader(t("tab1_price_chart"))
    norm = normalise_prices(prices)
    fig = go.Figure()
    for col in norm.columns:
        fig.add_trace(go.Scatter(x=norm.index, y=norm[col], name=col, mode="lines"))
    fig.update_layout(
        xaxis_title=t("tab1_x_date"),
        yaxis_title=t("tab1_y_value"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary statistics table
    st.subheader(t("tab1_stats"))
    stats = individual_fund_stats(mu, Sigma)
    stats["Sharpe Ratio"] = stats["Return"] / stats["Volatility"]
    display = stats.copy()
    display["Return"] = (display["Return"] * 100).round(2).astype(str) + "%"
    display["Volatility"] = (display["Volatility"] * 100).round(2).astype(str) + "%"
    display["Sharpe Ratio"] = display["Sharpe Ratio"].round(3)
    display.index.name = "Product"
    display = display.rename(columns={
        "Return": t("tab1_col_return"),
        "Volatility": t("tab1_col_vol"),
        "Sharpe Ratio": t("tab1_col_sharpe"),
    })
    st.dataframe(display, use_container_width=True)

    # Correlation heatmap
    st.subheader(t("tab1_corr"))
    corr = returns.corr()
    fig_corr = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu_r",
            zmin=-1,
            zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )
    fig_corr.update_layout(height=500, margin=dict(t=30, b=30))
    st.plotly_chart(fig_corr, use_container_width=True)

    # Variance-Covariance matrix
    with st.expander(t("tab1_cov")):
        Sigma_display = Sigma.round(6)
        Sigma_display.index.name = "Product"
        Sigma_display.columns.name = "Product"
        st.dataframe(Sigma_display, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 2 — Efficient Frontier
# ══════════════════════════════════════════════════════════════
with tab2:
    st.header(t("tab2_header"))

    prices2, returns2, mu2, Sigma2 = get_data()
    if prices2 is None:
        st.info(t("tab2_no_data"))
        st.stop()
    if not uploaded_files:
        st.caption(t("tab2_using_default"))

    mu_arr = mu2.values
    Sigma_arr = Sigma2.values
    fund_names = mu2.index.tolist()

    @st.cache_data(show_spinner=False)
    def _get_frontier(mu_bytes, Sigma_bytes, n, allow_short, n_points=200):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        return compute_efficient_frontier(mu_a, Sig_a, allow_short, n_points)

    def get_frontier(mu_a, Sig_a, allow_short):
        n = len(mu_a)
        return _get_frontier(mu_a.tobytes(), Sig_a.tobytes(), n, allow_short)

    def _frontier_plot(frontier_df, gmvp, fund_stats, title):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=frontier_df["volatility"] * 100,
            y=frontier_df["return"] * 100,
            mode="lines",
            name=t("tab2_frontier_label"),
            line=dict(color="#2196F3", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=fund_stats["Volatility"] * 100,
            y=fund_stats["Return"] * 100,
            mode="markers+text",
            name=t("tab2_funds_label"),
            marker=dict(color="#FF9800", size=10, symbol="circle"),
            text=fund_stats.index.tolist(),
            textposition="top right",
            textfont=dict(size=9),
        ))
        fig.add_trace(go.Scatter(
            x=[gmvp["volatility"] * 100],
            y=[gmvp["return"] * 100],
            mode="markers+text",
            name=t("tab2_gmvp_label"),
            marker=dict(color="#e74c3c", size=14, symbol="star"),
            text=[t("tab2_gmvp_label")],
            textposition="top right",
        ))
        fig.update_layout(
            title=title,
            xaxis_title=t("tab2_x_axis"),
            yaxis_title=t("tab2_y_axis"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=480,
            margin=dict(t=50, b=30),
        )
        return fig

    fund_stats = individual_fund_stats(mu2, Sigma2)
    col_a, col_b = st.columns(2)

    # ── With Short Sales ──
    with col_a:
        st.subheader(t("tab2_with_short"))
        with st.spinner(t("tab2_computing")):
            frontier_short = get_frontier(mu_arr, Sigma_arr, allow_short=True)
        gmvp_short = compute_gmvp(mu_arr, Sigma_arr, allow_short=True)
        fig_short = _frontier_plot(frontier_short, gmvp_short, fund_stats, t("tab2_with_short"))
        st.plotly_chart(fig_short, use_container_width=True)

        with st.expander(t("tab2_gmvp_short")):
            gmvp_df = pd.DataFrame({
                t("tab2_fund_col"): fund_names,
                t("tab2_weight_col"): (gmvp_short["weights"] * 100).round(2),
            }).sort_values(t("tab2_weight_col"), ascending=False)
            st.dataframe(gmvp_df, use_container_width=True)
            col1, col2 = st.columns(2)
            col1.metric(t("tab2_return_metric"), f"{gmvp_short['return']*100:.2f}%")
            col2.metric(t("tab2_vol_metric"), f"{gmvp_short['volatility']*100:.2f}%")

    # ── Without Short Sales ──
    with col_b:
        st.subheader(t("tab2_no_short"))
        with st.spinner(t("tab2_computing")):
            frontier_long = get_frontier(mu_arr, Sigma_arr, allow_short=False)
        gmvp_long = compute_gmvp(mu_arr, Sigma_arr, allow_short=False)
        fig_long = _frontier_plot(frontier_long, gmvp_long, fund_stats, t("tab2_no_short"))
        st.plotly_chart(fig_long, use_container_width=True)

        with st.expander(t("tab2_gmvp_long")):
            gmvp_df2 = pd.DataFrame({
                t("tab2_fund_col"): fund_names,
                t("tab2_weight_col"): (gmvp_long["weights"] * 100).round(2),
            }).sort_values(t("tab2_weight_col"), ascending=False)
            gmvp_df2 = gmvp_df2[gmvp_df2[t("tab2_weight_col")].abs() > 0.1]
            st.dataframe(gmvp_df2, use_container_width=True)
            col1, col2 = st.columns(2)
            col1.metric(t("tab2_return_metric"), f"{gmvp_long['return']*100:.2f}%")
            col2.metric(t("tab2_vol_metric"), f"{gmvp_long['volatility']*100:.2f}%")

    # Download frontier data
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        csv_short = frontier_short[["return", "volatility"]].to_csv(index=False)
        st.download_button(t("tab2_dl_short"), csv_short, "frontier_with_short.csv", "text/csv")
    with c2:
        csv_long = frontier_long[["return", "volatility"]].to_csv(index=False)
        st.download_button(t("tab2_dl_long"), csv_long, "frontier_no_short.csv", "text/csv")

# ══════════════════════════════════════════════════════════════
# TAB 3 — Risk Profile Questionnaire
# ══════════════════════════════════════════════════════════════
with tab3:
    st.header(t("tab3_header"))
    st.markdown(t("tab3_intro"))

    # Session state: answers stored as option indices (language-agnostic)
    if "q_index" not in st.session_state:
        st.session_state["q_index"] = 0
    if "answers" not in st.session_state:
        st.session_state["answers"] = [None] * len(QUESTIONS)

    n_q = len(QUESTIONS)
    q_idx = st.session_state["q_index"]

    # Progress bar
    answered = sum(1 for a in st.session_state["answers"] if a is not None)
    st.progress(
        answered / n_q,
        text=t("tab3_progress").format(cur=min(q_idx + 1, n_q), total=n_q),
    )

    if q_idx < n_q:
        q_en = QUESTIONS[q_idx]
        q_tr = t("questions")[q_idx]

        st.subheader(t("tab3_q_label").format(n=q_idx + 1, text=q_tr["text"]))

        # Default selection: use stored index (None → 0)
        stored_idx = st.session_state["answers"][q_idx]
        default_idx = stored_idx if stored_idx is not None else 0

        selected_text = st.radio(
            t("tab3_select"),
            options=q_tr["options"],
            index=default_idx,
            key=f"q_{q_idx}",
        )

        col_back, col_next = st.columns([1, 1])
        with col_back:
            if q_idx > 0:
                if st.button(t("tab3_back")):
                    st.session_state["q_index"] -= 1
                    st.rerun()
        with col_next:
            btn_label = t("tab3_next") if q_idx < n_q - 1 else t("tab3_submit")
            if st.button(btn_label, type="primary"):
                # Store the selected option index (not the text) — language-agnostic
                selected_idx = q_tr["options"].index(selected_text)
                st.session_state["answers"][q_idx] = selected_idx
                if q_idx < n_q - 1:
                    st.session_state["q_index"] += 1
                else:
                    st.session_state["q_index"] = n_q  # mark complete
                st.rerun()

    else:
        # Compute score from stored indices
        total_score = 0
        for i, q in enumerate(QUESTIONS):
            ans_idx = st.session_state["answers"][i]
            if ans_idx is not None:
                total_score += q["scores"][ans_idx]

        A = score_to_A(total_score)
        profile = translate_profile(describe_profile(A))
        st.session_state["A"] = A

        # Display result card
        st.success(t("tab3_complete"))
        st.markdown(
            f"""
            <div style="
                background-color:{profile['color']}22;
                border-left: 6px solid {profile['color']};
                padding: 20px 24px;
                border-radius: 8px;
                margin-bottom: 16px;
            ">
                <h2 style="color:{profile['color']}; margin:0">
                    {profile['emoji']} {profile['label']}
                </h2>
                <p style="margin-top:8px; font-size:1.05em">{profile['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        min_s, max_s = get_score_range()
        c1, c2, c3 = st.columns(3)
        c1.metric(t("tab3_score"), t("tab3_score_of").format(score=total_score, max=max_s))
        c2.metric(t("tab3_a_val"), f"{A:.1f}")
        c3.metric(t("tab3_profile_label"), profile["label"])

        st.divider()

        # Review answers
        with st.expander(t("tab3_review")):
            for i, q_en in enumerate(QUESTIONS):
                q_tr = t("questions")[i]
                ans_idx = st.session_state["answers"][i]
                ans_text = q_tr["options"][ans_idx] if ans_idx is not None else "—"
                score = q_en["scores"][ans_idx] if ans_idx is not None else "?"
                st.markdown(f"**Q{i+1}. {q_tr['text']}**  \n→ {ans_text} *(score: {score})*")

        if st.button(t("tab3_retake")):
            st.session_state["q_index"] = 0
            st.session_state["answers"] = [None] * n_q
            if "A" in st.session_state:
                del st.session_state["A"]
            st.rerun()

# ══════════════════════════════════════════════════════════════
# TAB 4 — Optimal Portfolio
# ══════════════════════════════════════════════════════════════
with tab4:
    st.header(t("tab4_header"))

    prices4, returns4, mu4, Sigma4 = get_data()
    if prices4 is None:
        st.info(t("tab4_no_data"))
        st.stop()

    if "A" not in st.session_state:
        st.info(t("tab4_no_profile"))
        st.stop()

    A = st.session_state["A"]
    profile4 = translate_profile(describe_profile(A))

    mu_arr4 = mu4.values
    Sigma_arr4 = Sigma4.values
    fund_names4 = mu4.index.tolist()

    st.markdown(t("tab4_using_profile").format(label=profile4["label"], A=A))

    A_override = st.slider(
        t("tab4_adjust_a"),
        min_value=1.0,
        max_value=8.0,
        value=float(A),
        step=0.1,
        help=t("tab4_adjust_help"),
    )

    opt_short_toggle = st.toggle(t("tab4_short_toggle"), value=allow_short)

    @st.cache_data(show_spinner=False)
    def _get_optimal(mu_bytes, Sigma_bytes, n, A, allow_short, names_key):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        return find_optimal_portfolio(mu_a, Sig_a, A, allow_short, list(names_key))

    n4 = len(mu_arr4)
    with st.spinner(t("tab4_optimising")):
        optimal = _get_optimal(
            mu_arr4.tobytes(),
            Sigma_arr4.tobytes(),
            n4,
            round(A_override, 2),
            opt_short_toggle,
            tuple(fund_names4),
        )

    if not optimal["success"]:
        st.warning(t("tab4_not_converged"))

    # ── Key metrics ──
    st.divider()
    m1, m2, m3, m4_col = st.columns(4)
    m1.metric(t("tab4_exp_return"), f"{optimal['return']*100:.2f}%")
    m2.metric(t("tab4_volatility"), f"{optimal['volatility']*100:.2f}%")
    m3.metric(t("tab4_utility"), f"{optimal['utility']:.4f}")
    m4_col.metric(t("tab4_sharpe"), f"{optimal['sharpe']:.3f}")

    st.divider()
    col_chart, col_table = st.columns([1.15, 1])

    alloc = optimal["allocation"]

    # ── Bar chart (handles long/short weights properly) ──
    with col_chart:
        st.subheader(t("tab4_alloc_title"))
        bar_alloc = alloc.copy()
        bar_alloc["Position"] = bar_alloc["Weight (%)"].apply(
            lambda w: t("tab4_long") if w >= 0 else t("tab4_short_pos")
        )
        bar_alloc["Display Fund"] = bar_alloc["Fund"].apply(_humanise_fund_label)
        bar_alloc = bar_alloc.sort_values("Weight (%)", ascending=False).reset_index(drop=True)

        fig_alloc = go.Figure()
        for pos_label, color in [(t("tab4_long"), "#f97316"), (t("tab4_short_pos"), "#2563eb")]:
            subset = bar_alloc[bar_alloc["Position"] == pos_label]
            if subset.empty:
                continue
            fig_alloc.add_trace(go.Bar(
                name=pos_label,
                x=subset["Weight (%)"].tolist(),
                y=subset["Fund"].tolist(),
                orientation="h",
                marker_color=color,
                text=subset["Weight (%)"].map(lambda w: f"{w:.2f}%").tolist(),
                textposition="outside",
                customdata=subset[["Display Fund", "Position", "Weight (%)"]].to_numpy(),
                hovertemplate=(
                    "%{customdata[0]}<br>"
                    f"{t('tab4_position')}: %{{customdata[1]}}<br>"
                    f"{t('tab4_weight_axis')}: %{{customdata[2]:.2f}}%<extra></extra>"
                ),
            ))

        max_abs_weight = max(float(bar_alloc["Weight (%)"].abs().max()), 1.0)
        fig_alloc.update_layout(
            barmode="relative",
            height=max(380, 34 * len(bar_alloc) + 120),
            margin=dict(t=20, b=30, l=10, r=50),
            legend_title_text=t("tab4_position"),
            yaxis=dict(
                categoryorder="array",
                categoryarray=bar_alloc["Fund"].tolist(),
                tickmode="array",
                tickvals=bar_alloc["Fund"].tolist(),
                ticktext=bar_alloc["Display Fund"].tolist(),
                autorange="reversed",
                automargin=True,
            ),
            xaxis=dict(
                title=t("tab4_weight_axis"),
                range=[-max_abs_weight * 1.2, max_abs_weight * 1.2],
                ticksuffix="%",
                zeroline=True,
                zerolinecolor="#d1d5db",
                zerolinewidth=2,
            ),
        )
        st.plotly_chart(fig_alloc, use_container_width=True)

    # ── Allocation table ──
    with col_table:
        st.subheader(t("tab4_alloc_table"))
        display_alloc = alloc[["Fund", "Weight (%)"]].rename(columns={"Fund": t("tab2_fund_col")})
        display_alloc["Weight (%)"] = display_alloc["Weight (%)"].apply(lambda x: f"{x:.2f}%")
        st.dataframe(display_alloc, use_container_width=True, hide_index=True)

        st.markdown(t("tab4_utility_decomp"))
        var_opt = optimal["volatility"] ** 2
        st.markdown(
            t("tab4_utility_formula").format(
                ret=optimal["return"] * 100,
                A=A_override,
                var=var_opt * 100,
                u=optimal["utility"],
            )
        )

    # ── Optimal point on frontier overlay ──
    st.divider()
    st.subheader(t("tab4_frontier_title"))

    @st.cache_data(show_spinner=False)
    def _get_frontier4(mu_bytes, Sigma_bytes, n, allow_short):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        return compute_efficient_frontier(mu_a, Sig_a, allow_short)

    frontier4 = _get_frontier4(mu_arr4.tobytes(), Sigma_arr4.tobytes(), n4, opt_short_toggle)
    fund_stats4 = individual_fund_stats(mu4, Sigma4)

    fig_overlay = go.Figure()
    fig_overlay.add_trace(go.Scatter(
        x=frontier4["volatility"] * 100,
        y=frontier4["return"] * 100,
        mode="lines",
        name=t("tab4_frontier_label"),
        line=dict(color="#2196F3", width=2),
    ))
    fig_overlay.add_trace(go.Scatter(
        x=fund_stats4["Volatility"] * 100,
        y=fund_stats4["Return"] * 100,
        mode="markers+text",
        name=t("tab4_funds_label"),
        marker=dict(color="#FF9800", size=8),
        text=fund_stats4.index.tolist(),
        textposition="top right",
        textfont=dict(size=8),
    ))
    fig_overlay.add_trace(go.Scatter(
        x=[optimal["volatility"] * 100],
        y=[optimal["return"] * 100],
        mode="markers+text",
        name=f"{t('tab4_optimal_label')} (A={A_override:.1f})",
        marker=dict(color="#9C27B0", size=16, symbol="diamond"),
        text=[t("tab4_optimal_label")],
        textposition="top right",
    ))
    fig_overlay.update_layout(
        xaxis_title=t("tab2_x_axis"),
        yaxis_title=t("tab2_y_axis"),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_overlay, use_container_width=True)

    # ── Sensitivity analysis ──
    st.divider()
    st.subheader(t("tab4_sens_title"))

    @st.cache_data(show_spinner=False)
    def _sensitivity(mu_bytes, Sigma_bytes, n, A_center, allow_short, names_key):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        return sensitivity_analysis(mu_a, Sig_a, A_center, allow_short, list(names_key))

    with st.spinner(t("tab4_sens_running")):
        sens_df = _sensitivity(
            mu_arr4.tobytes(),
            Sigma_arr4.tobytes(),
            n4,
            round(A_override, 2),
            opt_short_toggle,
            tuple(fund_names4),
        )

    fig_sens = go.Figure()
    for col in sens_df.columns[1:]:
        fig_sens.add_trace(go.Scatter(
            x=sens_df["A"],
            y=sens_df[col],
            name=col,
            mode="lines+markers",
            stackgroup="one",
        ))
    fig_sens.update_layout(
        xaxis_title=t("tab4_x_a"),
        yaxis_title=t("tab4_y_alloc"),
        height=380,
        yaxis_range=[0, 100],
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_sens, use_container_width=True)
    st.caption(t("tab4_sens_caption"))
