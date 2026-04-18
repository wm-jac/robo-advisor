"""
app.py  —  BMD5302 Robo-Advisor  (Streamlit)
Run with:  streamlit run app.py
"""

import json
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
from src.risk_assessment import (
    QUESTIONS,
    calculate_utility,
    describe_profile,
    get_score_range,
    score_to_A,
)

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
# Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Robo-Advisor")
    st.markdown("**BMD5302 Group Project**")
    st.divider()

    uploaded_files = st.file_uploader(
        "Upload fund price CSVs (FSMOne format)",
        type=["csv"],
        accept_multiple_files=True,
        help="Download historical prices from FSMOne Fund Selector. Each CSV = one fund.",
    )

    freq = st.selectbox(
        "Return frequency",
        options=["Daily", "Weekly", "Monthly"],
        index=0,
    )

    allow_short = st.toggle("Allow short sales", value=False)

    st.divider()
    st.caption("AY 2025/26 Semester 2")

# ──────────────────────────────────────────────────────────────
# Data loading (cached)
# ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_data(file_bytes_list: list[bytes], file_names: list[str], freq: str):
    """Cache-friendly wrapper: receives raw bytes so Streamlit can hash them."""
    import io
    file_objs = [io.BytesIO(b) for b in file_bytes_list]
    for fobj, name in zip(file_objs, file_names):
        fobj.name = name
    prices = load_all_funds(file_objs, file_names)
    returns = compute_returns(prices, method="log")
    mu, Sigma = annualise_stats(returns, freq=freq)
    return prices, returns, mu, Sigma


def _default_data_files() -> list[Path]:
    return sorted(path for path in DATA_DIR.glob("*.csv") if path.is_file())


def get_data():
    if uploaded_files:
        file_bytes = [f.read() for f in uploaded_files]
        for f in uploaded_files:
            f.seek(0)
        file_names = [Path(f.name).stem for f in uploaded_files]
        source = "uploaded data"
    else:
        data_files = _default_data_files()
        if not data_files:
            return None, None, None, None
        file_bytes = [path.read_bytes() for path in data_files]
        file_names = [path.stem for path in data_files]
        source = f"default CSVs in {DATA_DIR}"

    try:
        prices, returns, mu, Sigma = _load_data(
            file_bytes, file_names, freq
        )
        return prices, returns, mu, Sigma
    except Exception as e:
        st.error(f"Error loading {source}: {e}")
        return None, None, None, None


# ──────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Data & Funds", "🎯 Efficient Frontier", "🧠 Risk Profile", "💼 Optimal Portfolio"]
)

# ══════════════════════════════════════════════════════════════
# TAB 1 — Data & Funds
# ══════════════════════════════════════════════════════════════
with tab1:
    st.header("Fund Data Overview")

    if not uploaded_files:
        default_files = _default_data_files()
        if default_files:
            st.info(
                f"No uploaded files detected. Using **{len(default_files)} CSV files** "
                "from the local `data/` directory. Upload files in the sidebar to "
                "override this default dataset."
            )
        else:
            st.info(
                "Upload 10 fund price CSVs from **FSMOne Fund Selector** using the sidebar "
                "to get started, or place CSV files in the local `data/` directory. "
                "Each CSV should contain Date and Price columns."
            )
            st.markdown(
                """
                **How to download from FSMOne:**
                1. Go to [FSMOne Fund Selector](https://secure.fundsupermart.com/fsm/funds/fund-selector)
                2. Search for and select a fund
                3. Go to the **Price** tab and download historical data as CSV
                4. Repeat for 10 different funds
                """
            )
            st.stop()

    prices, returns, mu, Sigma = get_data()
    if prices is None:
        st.stop()

    data_source = "uploaded files" if uploaded_files else "`data/` directory"
    st.success(
        f"Loaded **{len(prices.columns)} funds** from {data_source} | "
        f"{prices.index[0].date()} → {prices.index[-1].date()} | "
        f"{len(prices)} observations"
    )

    # Normalised price chart
    st.subheader("Normalised Price Performance (rebased to 100)")
    norm = normalise_prices(prices)
    fig = go.Figure()
    for col in norm.columns:
        fig.add_trace(go.Scatter(x=norm.index, y=norm[col], name=col, mode="lines"))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value (rebased to 100)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary statistics table
    st.subheader("Fund Statistics (Annualised)")
    stats = individual_fund_stats(mu, Sigma)
    stats["Sharpe Ratio"] = stats["Return"] / stats["Volatility"]
    display = stats.copy()
    display["Return"] = (display["Return"] * 100).round(2).astype(str) + "%"
    display["Volatility"] = (display["Volatility"] * 100).round(2).astype(str) + "%"
    display["Sharpe Ratio"] = display["Sharpe Ratio"].round(3)
    st.dataframe(display, use_container_width=True)

    # Correlation heatmap
    st.subheader("Correlation Matrix")
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
    with st.expander("Variance-Covariance Matrix"):
        st.dataframe(Sigma.round(6), use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 2 — Efficient Frontier
# ══════════════════════════════════════════════════════════════
with tab2:
    st.header("Efficient Frontier")

    prices2, returns2, mu2, Sigma2 = get_data()
    if prices2 is None:
        st.info("Upload fund CSVs in the sidebar or place at least two CSV files in `data/` to continue.")
        st.stop()
    if not uploaded_files:
        st.caption("Using the default fund CSVs from the local `data/` directory.")

    mu_arr = mu2.values
    Sigma_arr = Sigma2.values
    fund_names = mu2.index.tolist()

    @st.cache_data(show_spinner="Computing efficient frontier…")
    def _get_frontier(mu_bytes, Sigma_bytes, n, allow_short, n_points=200):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        return compute_efficient_frontier(mu_a, Sig_a, allow_short, n_points)

    def get_frontier(mu_a, Sig_a, allow_short):
        n = len(mu_a)
        return _get_frontier(mu_a.tobytes(), Sig_a.tobytes(), n, allow_short)

    def _frontier_plot(frontier_df, gmvp, fund_stats, title):
        fig = go.Figure()

        # Frontier curve
        fig.add_trace(go.Scatter(
            x=frontier_df["volatility"] * 100,
            y=frontier_df["return"] * 100,
            mode="lines",
            name="Efficient Frontier",
            line=dict(color="#2196F3", width=2.5),
        ))

        # Individual funds
        fig.add_trace(go.Scatter(
            x=fund_stats["Volatility"] * 100,
            y=fund_stats["Return"] * 100,
            mode="markers+text",
            name="Individual Funds",
            marker=dict(color="#FF9800", size=10, symbol="circle"),
            text=fund_stats.index.tolist(),
            textposition="top right",
            textfont=dict(size=9),
        ))

        # GMVP
        fig.add_trace(go.Scatter(
            x=[gmvp["volatility"] * 100],
            y=[gmvp["return"] * 100],
            mode="markers+text",
            name="GMVP",
            marker=dict(color="#e74c3c", size=14, symbol="star"),
            text=["GMVP"],
            textposition="top right",
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Volatility (% annualised)",
            yaxis_title="Return (% annualised)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=480,
            margin=dict(t=50, b=30),
        )
        return fig

    fund_stats = individual_fund_stats(mu2, Sigma2)

    col_a, col_b = st.columns(2)

    # ── With Short Sales ──
    with col_a:
        st.subheader("With Short Sales")
        frontier_short = get_frontier(mu_arr, Sigma_arr, allow_short=True)
        gmvp_short = compute_gmvp(mu_arr, Sigma_arr, allow_short=True)
        fig_short = _frontier_plot(frontier_short, gmvp_short, fund_stats, "With Short Sales")
        st.plotly_chart(fig_short, use_container_width=True)

        with st.expander("GMVP Details — With Short Sales"):
            gmvp_df = pd.DataFrame({
                "Fund": fund_names,
                "Weight (%)": (gmvp_short["weights"] * 100).round(2),
            }).sort_values("Weight (%)", ascending=False)
            st.dataframe(gmvp_df, use_container_width=True)
            col1, col2 = st.columns(2)
            col1.metric("Return", f"{gmvp_short['return']*100:.2f}%")
            col2.metric("Volatility", f"{gmvp_short['volatility']*100:.2f}%")

    # ── Without Short Sales ──
    with col_b:
        st.subheader("Without Short Sales (Long-Only)")
        frontier_long = get_frontier(mu_arr, Sigma_arr, allow_short=False)
        gmvp_long = compute_gmvp(mu_arr, Sigma_arr, allow_short=False)
        fig_long = _frontier_plot(frontier_long, gmvp_long, fund_stats, "Without Short Sales")
        st.plotly_chart(fig_long, use_container_width=True)

        with st.expander("GMVP Details — Without Short Sales"):
            gmvp_df2 = pd.DataFrame({
                "Fund": fund_names,
                "Weight (%)": (gmvp_long["weights"] * 100).round(2),
            }).sort_values("Weight (%)", ascending=False)
            gmvp_df2 = gmvp_df2[gmvp_df2["Weight (%)"].abs() > 0.1]
            st.dataframe(gmvp_df2, use_container_width=True)
            col1, col2 = st.columns(2)
            col1.metric("Return", f"{gmvp_long['return']*100:.2f}%")
            col2.metric("Volatility", f"{gmvp_long['volatility']*100:.2f}%")

    # Download frontier data
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        csv_short = frontier_short[["return", "volatility"]].to_csv(index=False)
        st.download_button(
            "⬇️ Download Frontier (With Short Sales)",
            csv_short,
            "frontier_with_short.csv",
            "text/csv",
        )
    with c2:
        csv_long = frontier_long[["return", "volatility"]].to_csv(index=False)
        st.download_button(
            "⬇️ Download Frontier (Without Short Sales)",
            csv_long,
            "frontier_no_short.csv",
            "text/csv",
        )

# ══════════════════════════════════════════════════════════════
# TAB 3 — Risk Profile Questionnaire
# ══════════════════════════════════════════════════════════════
with tab3:
    st.header("Investor Risk Profile")
    st.markdown(
        "Answer the following questions honestly. Your answers will be used to determine "
        "your **risk aversion coefficient A** and personalised optimal portfolio."
    )

    # Initialise session state
    if "q_index" not in st.session_state:
        st.session_state["q_index"] = 0
    if "answers" not in st.session_state:
        st.session_state["answers"] = [None] * len(QUESTIONS)

    n_q = len(QUESTIONS)
    q_idx = st.session_state["q_index"]

    # Progress
    answered = sum(1 for a in st.session_state["answers"] if a is not None)
    st.progress(answered / n_q, text=f"Question {min(q_idx+1, n_q)} of {n_q}")

    if q_idx < n_q:
        q = QUESTIONS[q_idx]
        st.subheader(f"Question {q_idx + 1}: {q['text']}")

        current_answer = st.session_state["answers"][q_idx]
        default_idx = (
            q["options"].index(current_answer)
            if current_answer in q["options"]
            else 0
        )
        selected = st.radio(
            "Select your answer:",
            options=q["options"],
            index=default_idx,
            key=f"q_{q_idx}",
        )

        col_back, col_next = st.columns([1, 1])
        with col_back:
            if q_idx > 0:
                if st.button("← Back"):
                    st.session_state["q_index"] -= 1
                    st.rerun()
        with col_next:
            btn_label = "Next →" if q_idx < n_q - 1 else "Submit ✓"
            if st.button(btn_label, type="primary"):
                st.session_state["answers"][q_idx] = selected
                if q_idx < n_q - 1:
                    st.session_state["q_index"] += 1
                else:
                    st.session_state["q_index"] = n_q  # mark complete
                st.rerun()

    else:
        # Compute score
        total_score = 0
        for i, q in enumerate(QUESTIONS):
            ans = st.session_state["answers"][i]
            if ans in q["options"]:
                total_score += q["scores"][q["options"].index(ans)]

        A = score_to_A(total_score)
        profile = describe_profile(A)
        st.session_state["A"] = A
        st.session_state["profile"] = profile

        # Display results
        st.success("Questionnaire complete!")
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
                    {profile['emoji']} {profile['label']} Investor
                </h2>
                <p style="margin-top:8px; font-size:1.05em">{profile['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        min_s, max_s = get_score_range()
        c1.metric("Risk Score", f"{total_score} / {max_s}")
        c2.metric("Risk Aversion (A)", f"{A:.1f}")
        c3.metric("Profile", profile["label"])

        st.divider()

        # Show answers summary
        with st.expander("Review your answers"):
            for i, q in enumerate(QUESTIONS):
                ans = st.session_state["answers"][i]
                score = q["scores"][q["options"].index(ans)] if ans in q["options"] else "?"
                st.markdown(f"**Q{i+1}. {q['text']}**  \n→ {ans} *(score: {score})*")

        if st.button("Retake Questionnaire"):
            st.session_state["q_index"] = 0
            st.session_state["answers"] = [None] * n_q
            if "A" in st.session_state:
                del st.session_state["A"]
            st.rerun()

# ══════════════════════════════════════════════════════════════
# TAB 4 — Optimal Portfolio
# ══════════════════════════════════════════════════════════════
with tab4:
    st.header("Optimal Portfolio")

    prices4, returns4, mu4, Sigma4 = get_data()
    if prices4 is None:
        st.info("Upload fund CSVs in the sidebar or place at least two CSV files in `data/` to continue.")
        st.stop()

    if "A" not in st.session_state:
        st.info("Please complete the **Risk Profile** questionnaire in Tab 3 first.")
        st.stop()

    A = st.session_state["A"]
    profile = st.session_state.get("profile", describe_profile(A))

    mu_arr4 = mu4.values
    Sigma_arr4 = Sigma4.values
    fund_names4 = mu4.index.tolist()

    # Allow overriding A
    st.markdown(
        f"Using **{profile['label']} investor profile** with risk aversion A = **{A:.1f}**"
    )
    A_override = st.slider(
        "Adjust A (risk aversion) to explore",
        min_value=1.0,
        max_value=8.0,
        value=float(A),
        step=0.1,
        help="A=1 is very aggressive; A=8 is very conservative. The default is from your questionnaire.",
    )

    opt_short_toggle = st.toggle("Allow short sales in optimal portfolio", value=allow_short)

    @st.cache_data(show_spinner="Optimising portfolio…")
    def _get_optimal(mu_bytes, Sigma_bytes, n, A, allow_short, names_key):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        names = list(names_key)
        return find_optimal_portfolio(mu_a, Sig_a, A, allow_short, names)

    n4 = len(mu_arr4)
    optimal = _get_optimal(
        mu_arr4.tobytes(),
        Sigma_arr4.tobytes(),
        n4,
        round(A_override, 2),
        opt_short_toggle,
        tuple(fund_names4),
    )

    if not optimal["success"]:
        st.warning("Optimisation did not fully converge. Results may be approximate.")

    # ── Key metrics ──
    st.divider()
    m1, m2, m3, m4_col = st.columns(4)
    m1.metric("Expected Return", f"{optimal['return']*100:.2f}%")
    m2.metric("Volatility", f"{optimal['volatility']*100:.2f}%")
    m3.metric("Utility (U)", f"{optimal['utility']:.4f}")
    m4_col.metric("Sharpe Ratio", f"{optimal['sharpe']:.3f}")

    st.divider()
    col_pie, col_table = st.columns([1, 1])

    # Pie chart
    with col_pie:
        st.subheader("Portfolio Allocation")
        alloc = optimal["allocation"]
        fig_pie = go.Figure(go.Pie(
            labels=alloc["Fund"],
            values=alloc["Weight (%)"],
            hole=0.35,
            textinfo="label+percent",
            hoverinfo="label+value",
        ))
        fig_pie.update_layout(height=380, margin=dict(t=20, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Allocation table
    with col_table:
        st.subheader("Allocation Table")
        display_alloc = alloc[["Fund", "Weight (%)"]].copy()
        display_alloc["Weight (%)"] = display_alloc["Weight (%)"].apply(lambda x: f"{x:.2f}%")
        st.dataframe(display_alloc, use_container_width=True, hide_index=True)

        # Utility breakdown
        st.markdown("**Utility Decomposition**")
        var_opt = optimal["volatility"] ** 2
        st.markdown(
            f"U = r − (A/2)·σ²  \n"
            f"U = {optimal['return']*100:.2f}% − ({A_override:.1f}/2)·{var_opt*100:.4f}%  \n"
            f"U = **{optimal['utility']:.4f}**"
        )

    # Optimal point on frontier overlay
    st.divider()
    st.subheader("Optimal Portfolio on the Efficient Frontier")

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
        name="Efficient Frontier",
        line=dict(color="#2196F3", width=2),
    ))
    fig_overlay.add_trace(go.Scatter(
        x=fund_stats4["Volatility"] * 100,
        y=fund_stats4["Return"] * 100,
        mode="markers+text",
        name="Individual Funds",
        marker=dict(color="#FF9800", size=8),
        text=fund_stats4.index.tolist(),
        textposition="top right",
        textfont=dict(size=8),
    ))
    fig_overlay.add_trace(go.Scatter(
        x=[optimal["volatility"] * 100],
        y=[optimal["return"] * 100],
        mode="markers+text",
        name=f"Optimal (A={A_override:.1f})",
        marker=dict(color="#9C27B0", size=16, symbol="diamond"),
        text=["★ Optimal"],
        textposition="top right",
    ))
    fig_overlay.update_layout(
        xaxis_title="Volatility (% annualised)",
        yaxis_title="Return (% annualised)",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_overlay, use_container_width=True)

    # Sensitivity analysis
    st.divider()
    st.subheader("Sensitivity Analysis — How A Affects Allocation")

    @st.cache_data(show_spinner="Running sensitivity analysis…")
    def _sensitivity(mu_bytes, Sigma_bytes, n, A_center, allow_short, names_key):
        mu_a = np.frombuffer(mu_bytes).reshape(n)
        Sig_a = np.frombuffer(Sigma_bytes).reshape(n, n)
        return sensitivity_analysis(mu_a, Sig_a, A_center, allow_short, list(names_key))

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
        xaxis_title="Risk Aversion A",
        yaxis_title="Allocation (%)",
        height=380,
        yaxis_range=[0, 100],
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_sens, use_container_width=True)
    st.caption(
        "Stacked area chart showing how optimal fund allocations shift as A varies. "
        "Higher A = more conservative = lower-volatility funds dominate."
    )
