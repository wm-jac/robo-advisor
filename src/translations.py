"""
translations.py
All UI strings for English (en) and Simplified Chinese (zh).
"""

# Maps English profile label -> translation key suffix
PROFILE_KEY_MAP = {
    "Very Conservative": "very_conservative",
    "Conservative": "conservative",
    "Moderate": "moderate",
    "Aggressive": "aggressive",
    "Very Aggressive": "very_aggressive",
}

TRANSLATIONS: dict[str, dict] = {
    # ──────────────────────────────────────────────
    # ENGLISH
    # ──────────────────────────────────────────────
    "en": {
        # Sidebar
        "title": "📈 Robo-Advisor",
        "subtitle": "BMD5302 Group Project",
        "upload_label": "Upload fund price CSVs (FSMOne format)",
        "upload_help": "Download historical prices from FSMOne Fund Selector. Each CSV = one fund.",
        "freq_label": "Return frequency",
        "freq_options": ["Daily", "Weekly", "Monthly"],
        "allow_short": "Allow short sales",
        "semester": "AY 2025/26 Semester 2",
        "risk_free_source": (
            "Risk-free rate: {rate:.2f}% p.a. from [MAS 1-Year T-bill]({source_url}) "
            "({issue_code}, as of {as_of})."
        ),
        "risk_free_error": (
            "Could not fetch the MAS 1-Year T-bill risk-free rate ({e}). "
            "Sharpe ratios use 0.00%."
        ),

        # Tabs
        "tab1": "📊 Data & Funds",
        "tab2": "🎯 Efficient Frontier",
        "tab3": "🧠 Risk Profile",
        "tab4": "💼 Optimal Portfolio",

        # Tab 1
        "tab1_header": "Fund Data Overview",
        "tab1_upload_info": (
            "Upload 10 fund price CSVs from **FSMOne Fund Selector** using the sidebar "
            "to get started. Each CSV should contain Date and Price columns."
        ),
        "tab1_how_to": "**How to download from FSMOne:**",
        "tab1_steps": (
            "1. Go to [FSMOne Fund Selector](https://secure.fundsupermart.com/fsm/funds/fund-selector)\n"
            "2. Search for and select a fund\n"
            "3. Go to the **Price** tab and download historical data as CSV\n"
            "4. Repeat for 10 different funds"
        ),
        "tab1_using_default": (
            "No uploaded files detected. Using **{n} CSV files** from the local `data/` "
            "directory. Upload files in the sidebar to override this default dataset."
        ),
        "tab1_source_upload": "uploaded files",
        "tab1_source_local": "local `data/` directory",
        "tab1_loaded": "Loaded **{n} funds** from {source} | {start} → {end} | {obs} observations",
        "tab1_price_chart": "Normalised Price Performance (rebased to 100)",
        "tab1_x_date": "Date",
        "tab1_y_value": "Value (rebased to 100)",
        "tab1_stats": "Fund Statistics (Annualised)",
        "tab1_col_return": "Return",
        "tab1_col_vol": "Volatility",
        "tab1_col_sharpe": "Sharpe Ratio",
        "tab1_corr": "Correlation Matrix",
        "tab1_cov": "Variance-Covariance Matrix",
        "tab1_error": "Error loading data: {e}",

        # Tab 2
        "tab2_header": "Efficient Frontier",
        "tab2_no_data": "Upload fund CSVs in the sidebar or place CSV files in the local `data/` directory to continue.",
        "tab2_using_default": "Using the default fund CSVs from the local `data/` directory.",
        "tab2_with_short": "With Short Sales",
        "tab2_no_short": "Without Short Sales (Long-Only)",
        "tab2_gmvp_short": "GMVP Details — With Short Sales",
        "tab2_gmvp_long": "GMVP Details — Without Short Sales",
        "tab2_fund_col": "Product",
        "tab2_weight_col": "Weight (%)",
        "tab2_return_metric": "Return",
        "tab2_vol_metric": "Volatility",
        "tab2_dl_short": "⬇️ Download Frontier (With Short Sales)",
        "tab2_dl_long": "⬇️ Download Frontier (Without Short Sales)",
        "tab2_computing": "Computing efficient frontier…",
        "tab2_x_axis": "Volatility (% annualised)",
        "tab2_y_axis": "Return (% annualised)",
        "tab2_frontier_label": "Efficient Frontier",
        "tab2_funds_label": "Individual Funds",
        "tab2_gmvp_label": "GMVP",

        # Tab 3
        "tab3_header": "Investor Risk Profile",
        "tab3_intro": (
            "Answer the following questions honestly. Your answers will be used to determine "
            "your **risk aversion coefficient A** and personalised optimal portfolio."
        ),
        "tab3_progress": "Question {cur} of {total}",
        "tab3_q_label": "Question {n}: {text}",
        "tab3_select": "Select your answer:",
        "tab3_back": "← Back",
        "tab3_next": "Next →",
        "tab3_submit": "Submit ✓",
        "tab3_complete": "Questionnaire complete!",
        "tab3_score": "Risk Score",
        "tab3_a_val": "Risk Aversion (A)",
        "tab3_profile_label": "Profile",
        "tab3_score_of": "{score} / {max}",
        "tab3_review": "Review your answers",
        "tab3_retake": "Retake Questionnaire",

        # Tab 4
        "tab4_header": "Optimal Portfolio",
        "tab4_no_data": "Upload fund CSVs in the sidebar or place CSV files in the local `data/` directory to continue.",
        "tab4_weight_axis": "Portfolio weight (%)",
        "tab4_position": "Position",
        "tab4_long": "Long",
        "tab4_short_pos": "Short",
        "tab4_no_profile": "Please complete the **Risk Profile** questionnaire in Tab 3 first.",
        "tab4_using_profile": "Using **{label} investor profile** with risk aversion A = **{A:.1f}**",
        "tab4_adjust_a": "Adjust A (risk aversion) to explore",
        "tab4_adjust_help": "A=1 is very aggressive; A=8 is very conservative. The default is from your questionnaire.",
        "tab4_short_toggle": "Allow short sales in optimal portfolio",
        "tab4_optimising": "Optimising portfolio…",
        "tab4_not_converged": "Optimisation did not fully converge. Results may be approximate.",
        "tab4_exp_return": "Expected Return",
        "tab4_volatility": "Volatility",
        "tab4_utility": "Utility (U)",
        "tab4_sharpe": "Sharpe Ratio",
        "tab4_alloc_title": "Portfolio Allocation",
        "tab4_alloc_table": "Allocation Table",
        "tab4_utility_decomp": "**Utility Decomposition**",
        "tab4_utility_formula": (
            "U = r − (A/2)·σ²  \n"
            "U = {ret:.2f}% − ({A:.1f}/2)·{var:.4f}%  \n"
            "U = **{u:.4f}**"
        ),
        "tab4_frontier_title": "Optimal Portfolio on the Efficient Frontier",
        "tab4_sens_title": "Sensitivity Analysis — How A Affects Allocation",
        "tab4_sens_running": "Running sensitivity analysis…",
        "tab4_x_a": "Risk Aversion A",
        "tab4_y_alloc": "Allocation (%)",
        "tab4_sens_caption": (
            "Stacked area chart showing how optimal fund allocations shift as A varies. "
            "Higher A = more conservative = lower-volatility funds dominate."
        ),
        "tab4_optimal_label": "★ Optimal",
        "tab4_frontier_label": "Efficient Frontier",
        "tab4_funds_label": "Individual Funds",

        # Investor profiles
        "profile_very_conservative_label": "Very Conservative",
        "profile_very_conservative_desc": (
            "You prioritise capital preservation above all else. "
            "Your portfolio will focus heavily on low-volatility assets."
        ),
        "profile_conservative_label": "Conservative",
        "profile_conservative_desc": (
            "You are cautious about risk and prefer stable, income-generating investments "
            "over high-growth opportunities."
        ),
        "profile_moderate_label": "Moderate",
        "profile_moderate_desc": (
            "You seek a balance between growth and stability, "
            "accepting some volatility in exchange for reasonable returns."
        ),
        "profile_aggressive_label": "Aggressive",
        "profile_aggressive_desc": (
            "You are comfortable with significant market swings "
            "in pursuit of strong long-term capital growth."
        ),
        "profile_very_aggressive_label": "Very Aggressive",
        "profile_very_aggressive_desc": (
            "You pursue maximum returns and can tolerate large drawdowns. "
            "Your portfolio will be concentrated in high-growth assets."
        ),

        # Risk questionnaire questions & options
        "questions": [
            {
                "text": "What is your primary investment time horizon?",
                "options": [
                    "Less than 1 year",
                    "1 – 3 years",
                    "3 – 5 years",
                    "5 – 10 years",
                    "More than 10 years",
                ],
            },
            {
                "text": (
                    "Imagine your portfolio drops 20% in value over three months. "
                    "What would you most likely do?"
                ),
                "options": [
                    "Sell everything to prevent further losses",
                    "Sell some investments to reduce risk",
                    "Do nothing and wait for recovery",
                    "Buy more to take advantage of lower prices",
                ],
            },
            {
                "text": "What is the maximum loss you could accept in a single year without losing sleep?",
                "options": [
                    "I cannot tolerate any loss",
                    "Up to 5%",
                    "Up to 10%",
                    "Up to 20%",
                    "More than 20%",
                ],
            },
            {
                "text": "What is your primary investment goal?",
                "options": [
                    "Preserve my capital at all costs",
                    "Generate steady income with minimal risk",
                    "Balance between growth and income",
                    "Achieve long-term capital growth",
                    "Maximise returns, accepting high risk",
                ],
            },
            {
                "text": "How stable is your current income?",
                "options": [
                    "Very unstable – I rely on investments for daily expenses",
                    "Somewhat unstable – irregular income",
                    "Moderate – my income covers needs but little savings",
                    "Stable – salaried with regular savings",
                    "Very stable – high income with substantial savings",
                ],
            },
            {
                "text": "How would you describe your investment experience?",
                "options": [
                    "None – this is my first investment",
                    "Beginner – I have bought a few funds or ETFs",
                    "Intermediate – I actively manage a diversified portfolio",
                    "Experienced – I trade individual stocks and use derivatives",
                    "Expert – I have professional investment experience",
                ],
            },
            {
                "text": "How many months of living expenses do you have set aside as an emergency fund?",
                "options": [
                    "Less than 1 month",
                    "1 – 3 months",
                    "3 – 6 months",
                    "More than 6 months",
                ],
            },
        ],
    },

    # ──────────────────────────────────────────────
    # SIMPLIFIED CHINESE
    # ──────────────────────────────────────────────
    "zh": {
        # Sidebar
        "title": "📈 智能投顾",
        "subtitle": "BMD5302 小组项目",
        "upload_label": "上传基金价格CSV文件（FSMOne格式）",
        "upload_help": "从FSMOne基金筛选器下载历史价格，每个CSV对应一支基金。",
        "freq_label": "收益率频率",
        "freq_options": ["日频", "周频", "月频"],
        "allow_short": "允许卖空",
        "semester": "2025/26学年 第二学期",
        "risk_free_source": (
            "无风险利率：[MAS 1年期国库券]({source_url}) {rate:.2f}% p.a."
            "（{issue_code}，截至 {as_of}）。"
        ),
        "risk_free_error": (
            "无法获取MAS 1年期国库券无风险利率（{e}）。"
            "夏普比率将使用 0.00%。"
        ),

        # Tabs
        "tab1": "📊 数据与基金",
        "tab2": "🎯 有效前沿",
        "tab3": "🧠 风险评估",
        "tab4": "💼 最优组合",

        # Tab 1
        "tab1_header": "基金数据概览",
        "tab1_upload_info": (
            "请通过侧边栏上传来自 **FSMOne基金筛选器** 的10个基金CSV文件以开始使用。"
            "每个CSV应包含日期和价格列。"
        ),
        "tab1_how_to": "**如何从FSMOne下载数据：**",
        "tab1_steps": (
            "1. 前往 [FSMOne基金筛选器](https://secure.fundsupermart.com/fsm/funds/fund-selector)\n"
            "2. 搜索并选择一支基金\n"
            "3. 进入 **价格** 标签页，以CSV格式下载历史数据\n"
            "4. 重复以上步骤，共选择10支不同基金"
        ),
        "tab1_using_default": (
            "未检测到上传文件。正在使用本地`data/`目录中的 **{n} 个CSV文件**。"
            "可在侧边栏上传文件以覆盖默认数据集。"
        ),
        "tab1_source_upload": "已上传的文件",
        "tab1_source_local": "本地`data/`目录",
        "tab1_loaded": "已从{source}加载 **{n} 支基金** | {start} → {end} | 共 {obs} 个观测值",
        "tab1_price_chart": "标准化价格走势（以100为基准）",
        "tab1_x_date": "日期",
        "tab1_y_value": "价值（以100为基准）",
        "tab1_stats": "基金统计数据（年化）",
        "tab1_col_return": "收益率",
        "tab1_col_vol": "波动率",
        "tab1_col_sharpe": "夏普比率",
        "tab1_corr": "相关性矩阵",
        "tab1_cov": "方差-协方差矩阵",
        "tab1_error": "数据加载失败：{e}",

        # Tab 2
        "tab2_header": "有效前沿",
        "tab2_no_data": "请在侧边栏上传基金CSV文件，或将CSV文件放入本地`data/`目录以继续。",
        "tab2_using_default": "正在使用本地`data/`目录中的默认基金CSV文件。",
        "tab2_with_short": "允许卖空",
        "tab2_no_short": "不允许卖空（仅多头）",
        "tab2_gmvp_short": "全局最小方差组合详情 — 允许卖空",
        "tab2_gmvp_long": "全局最小方差组合详情 — 不允许卖空",
        "tab2_fund_col": "产品",
        "tab2_weight_col": "权重 (%)",
        "tab2_return_metric": "收益率",
        "tab2_vol_metric": "波动率",
        "tab2_dl_short": "⬇️ 下载有效前沿数据（允许卖空）",
        "tab2_dl_long": "⬇️ 下载有效前沿数据（不允许卖空）",
        "tab2_computing": "正在计算有效前沿…",
        "tab2_x_axis": "波动率（%，年化）",
        "tab2_y_axis": "收益率（%，年化）",
        "tab2_frontier_label": "有效前沿",
        "tab2_funds_label": "个别基金",
        "tab2_gmvp_label": "全局最小方差",

        # Tab 3
        "tab3_header": "投资者风险评估",
        "tab3_intro": (
            "请如实回答以下问题。您的答案将用于确定您的**风险厌恶系数A**及个性化最优投资组合。"
        ),
        "tab3_progress": "第 {cur} 题，共 {total} 题",
        "tab3_q_label": "第 {n} 题：{text}",
        "tab3_select": "请选择您的答案：",
        "tab3_back": "← 上一题",
        "tab3_next": "下一题 →",
        "tab3_submit": "提交 ✓",
        "tab3_complete": "问卷已完成！",
        "tab3_score": "风险评分",
        "tab3_a_val": "风险厌恶系数（A）",
        "tab3_profile_label": "风险类型",
        "tab3_score_of": "{score} / {max}",
        "tab3_review": "查看您的答案",
        "tab3_retake": "重新作答",

        # Tab 4
        "tab4_header": "最优投资组合",
        "tab4_no_data": "请在侧边栏上传基金CSV文件，或将CSV文件放入本地`data/`目录以继续。",
        "tab4_weight_axis": "组合权重 (%)",
        "tab4_position": "持仓方向",
        "tab4_long": "多头",
        "tab4_short_pos": "空头",
        "tab4_no_profile": "请先在第3标签页完成**风险评估**问卷。",
        "tab4_using_profile": "当前使用**{label}型投资者**配置，风险厌恶系数 A = **{A:.1f}**",
        "tab4_adjust_a": "调整 A（风险厌恶系数）以探索",
        "tab4_adjust_help": "A=1 最激进；A=8 最保守。默认值来自您的问卷结果。",
        "tab4_short_toggle": "在最优组合中允许卖空",
        "tab4_optimising": "正在优化投资组合…",
        "tab4_not_converged": "优化未完全收敛，结果可能为近似值。",
        "tab4_exp_return": "预期收益率",
        "tab4_volatility": "波动率",
        "tab4_utility": "效用值（U）",
        "tab4_sharpe": "夏普比率",
        "tab4_alloc_title": "投资组合配置",
        "tab4_alloc_table": "配置明细",
        "tab4_utility_decomp": "**效用函数分解**",
        "tab4_utility_formula": (
            "U = r − (A/2)·σ²  \n"
            "U = {ret:.2f}% − ({A:.1f}/2)·{var:.4f}%  \n"
            "U = **{u:.4f}**"
        ),
        "tab4_frontier_title": "最优组合在有效前沿上的位置",
        "tab4_sens_title": "敏感性分析 — A值对配置的影响",
        "tab4_sens_running": "正在运行敏感性分析…",
        "tab4_x_a": "风险厌恶系数 A",
        "tab4_y_alloc": "配置比例 (%)",
        "tab4_sens_caption": (
            "堆叠面积图展示了随A值变化，各基金最优配置比例的变动情况。"
            "A值越高 = 越保守 = 低波动性基金占比越大。"
        ),
        "tab4_optimal_label": "★ 最优",
        "tab4_frontier_label": "有效前沿",
        "tab4_funds_label": "个别基金",

        # Investor profiles
        "profile_very_conservative_label": "极度保守",
        "profile_very_conservative_desc": (
            "您将资本保全置于首位，投资组合将以低波动性资产为主。"
        ),
        "profile_conservative_label": "保守",
        "profile_conservative_desc": (
            "您对风险持谨慎态度，偏好稳定的收益型投资，而非追求高增长机会。"
        ),
        "profile_moderate_label": "稳健",
        "profile_moderate_desc": (
            "您寻求增长与稳定之间的平衡，愿意承受一定波动以换取合理回报。"
        ),
        "profile_aggressive_label": "进取",
        "profile_aggressive_desc": (
            "您能够承受较大的市场波动，以追求长期强劲的资本增值。"
        ),
        "profile_very_aggressive_label": "极度进取",
        "profile_very_aggressive_desc": (
            "您追求最高回报，能够承受大幅回撤，投资组合将集中于高增长资产。"
        ),

        # Risk questionnaire questions & options
        "questions": [
            {
                "text": "您的主要投资期限是多久？",
                "options": [
                    "少于1年",
                    "1 – 3年",
                    "3 – 5年",
                    "5 – 10年",
                    "超过10年",
                ],
            },
            {
                "text": "假设您的投资组合在三个月内跌值20%，您最可能采取什么行动？",
                "options": [
                    "卖出所有持仓以防止进一步损失",
                    "卖出部分投资以降低风险",
                    "什么都不做，等待市场回升",
                    "趁低价买入更多",
                ],
            },
            {
                "text": "您在一年内可以承受的最大亏损是多少（不影响睡眠）？",
                "options": [
                    "我无法承受任何亏损",
                    "最多5%",
                    "最多10%",
                    "最多20%",
                    "超过20%",
                ],
            },
            {
                "text": "您的主要投资目标是什么？",
                "options": [
                    "不惜一切保本",
                    "以最低风险产生稳定收益",
                    "增长与收益并重",
                    "追求长期资本增值",
                    "追求最高回报，接受高风险",
                ],
            },
            {
                "text": "您目前的收入稳定性如何？",
                "options": [
                    "非常不稳定——依赖投资支付日常开销",
                    "较不稳定——收入不规律",
                    "一般——收入够用但储蓄有限",
                    "稳定——有固定工资和定期储蓄",
                    "非常稳定——高收入且有大量储蓄",
                ],
            },
            {
                "text": "您如何描述自己的投资经验？",
                "options": [
                    "无——这是我第一次投资",
                    "初学者——购买过少量基金或ETF",
                    "中级——主动管理多元化投资组合",
                    "有经验——交易个股并使用衍生工具",
                    "专家——具有专业投资经验",
                ],
            },
            {
                "text": "您存有多少个月的生活费作为紧急备用金？",
                "options": [
                    "不足1个月",
                    "1 – 3个月",
                    "3 – 6个月",
                    "超过6个月",
                ],
            },
        ],
    },
}
