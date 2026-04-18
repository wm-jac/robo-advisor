# 15-Minute Demonstration Video Script

Project: BMD5302 Robo-Advisor  
Target duration: 15 minutes  
Recommended setup before recording:

1. Start backend: `python3 -m uvicorn backend.main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run preview`
3. Open `http://localhost:3000`
4. Keep the `docs/project_report.md` result tables nearby for reference.

## 0:00-0:45 - Opening and Project Objective

Visual: Cover slide or app landing on the Funds page.

Script:

"Hello, we are Group 8, and this is our BMD5302 Financial Modeling project: a web-based robo-advisor. The objective is to turn the Markowitz efficient frontier and investor risk aversion framework into an interactive application. The app loads ten FSMOne fund products, computes return and covariance inputs, compares portfolios with and without short sales, asks an investor risk questionnaire, and recommends the utility-maximising portfolio."

"The project has four main parts: data selection and statistical analysis, efficient frontier construction, investor risk assessment, and a digital platform with a live demonstration."

## 0:45-1:45 - Architecture and Repository Structure

Visual: Briefly show repository tree or README.

Script:

"The project is implemented as a full web application. The backend is in `backend/main.py` using FastAPI. The reusable financial modelling logic is in `src/`: `data_loader.py` loads FSMOne CSVs and computes returns, `portfolio.py` computes the efficient frontier and GMVP, `optimizer.py` computes the utility-maximising portfolio, `risk_assessment.py` defines the questionnaire and maps scores to the risk-aversion coefficient A, and `risk_free_rate.py` fetches the MAS 1-year T-bill yield used in Sharpe ratios."

"The frontend is in `frontend/` and is built with Next.js. There are four user pages: Funds, Frontier, Risk Profile, and Portfolio. Shared state is managed in `frontend/lib/store.ts`, while API calls are centralised in `frontend/lib/api.ts`."

"The `data/` folder contains the ten CSV files used for the default demonstration, and `scripts/download_fsmone_funds.py` can download the default basket from FSMOne."

## 1:45-3:00 - Why These 10 Funds Were Chosen

Visual: Funds page or a slide listing the ten funds.

Script:

"The project statement asks us to select ten FSMOne funds. We selected a diversified basket rather than ten funds from the same market or sector. The basket includes Singapore equities, ASEAN equities, US equities, Japan equities, emerging markets, global dividend equities, global technology, artificial intelligence, world energy, and world gold."

"The reason is that efficient frontier analysis depends heavily on covariance and diversification. If all ten products move together, the frontier is less informative. Here, we intentionally combine local, regional, developed-market, emerging-market, sector, income, growth, and commodity-linked exposures. For example, Singapore and ASEAN equities are related, while gold and energy add sector and commodity sensitivity. Global dividend exposure gives a more defensive equity component, and technology and AI provide growth-oriented exposures."

## 3:00-5:00 - Data Loading and Statistics

Visual: Funds page with default data loaded.

Script:

"On the Funds page, the app can either use the bundled default CSVs or accept uploaded FSMOne price CSV files. If no uploaded files are provided, it automatically loads the ten CSVs from the local `data/` directory."

"For this demonstration, the common aligned dataset runs from 4 January 2021 to 31 December 2025, with 1,298 price observations and 1,297 return observations."

"The backend computes daily log returns using the formula r equals log of price today divided by price yesterday. These returns are annualised using a 252 trading-day factor. The expected return vector is the average daily log return multiplied by 252, and the covariance matrix is the daily return covariance matrix multiplied by 252."

"The page shows performance cards, a normalised price chart rebased to 100, a statistics table, and a correlation heatmap. The Sharpe ratios are calculated as excess return over the MAS 1-year T-bill yield fetched by the backend, with a 0 percent fallback only if that fetch is unavailable."

"In the sample data, Eastspring Japan Dynamic has the highest annualised return at about 21.15 percent with volatility of 16.75 percent. Singapore Equity has annualised return of about 13.18 percent and volatility of 10.98 percent. Emerging Markets had a slightly negative annualised return over the period."

## 5:00-7:30 - Efficient Frontier and GMVP

Visual: Navigate to the Frontier page.

Script:

"Next, we move to the Efficient Frontier page. This page computes the frontier under two assumptions: first, long-only portfolios where all weights must be between zero and one; second, portfolios where short selling is allowed."

"The optimisation problem is to minimise portfolio variance for a sequence of target returns. Portfolio return is w transpose mu, and portfolio variance is w transpose Sigma w. For the long-only case, each weight is constrained between zero and one. For the short-allowed case, individual weights can be negative or above one, as long as the total weights sum to one."

"The charts show volatility on the x-axis and expected return on the y-axis. Individual funds appear as points, and the Global Minimum Variance Portfolio is marked separately."

"For the bundled data, the long-only GMVP has expected return of 6.71 percent and volatility of 8.40 percent. Its main allocations are about 46.35 percent to Global Dividend, 33.03 percent to ASEAN Equity, 19.40 percent to Singapore Equity, and 1.22 percent to Gold."

"When short sales are allowed, GMVP volatility falls slightly to 8.04 percent, with expected return of 6.33 percent. This happens because the model can short some higher-risk or covariance-heavy assets, such as Global Technology and AI, to reduce total variance."

"This comparison is important because it shows how relaxing portfolio constraints changes the feasible set. Shorting can improve the mathematical frontier, but it may be less practical for retail robo-advisory use."

## 7:30-9:30 - Risk Questionnaire and Risk Aversion

Visual: Navigate to Risk Profile page. Demonstrate a few answers, or show completed profile.

Script:

"The next part is investor risk assessment. The app uses a ten-question questionnaire covering investment time horizon, reaction to drawdowns, loss tolerance, investment objective, income stability, investment experience, emergency savings, reaction to volatile returns, proportion of savings invested, and attitude toward uncertain returns."

"Each answer has a score. Higher total scores mean higher risk tolerance. The backend maps the total score into the risk-aversion coefficient A. The score range is 14 to 48, and A ranges from 8 for the most conservative investor to 1 for the most aggressive investor."

"The formula is: A equals 8 minus the normalised questionnaire score times 7. This gives a transparent link between behavioural answers and the utility function."

"The profile labels are Very Conservative, Conservative, Moderate, Aggressive, and Very Aggressive. In the optimisation formula, a higher A penalises variance more strongly, so the model will prefer lower-risk portfolios. A lower A penalises risk less, so the model accepts more volatility in exchange for higher expected return."

"For the sample portfolio construction in our report, a total score of 24 maps to A equals 5.94, which is a Conservative profile."

## 9:30-12:30 - Optimal Portfolio Without Shorting

Visual: Navigate to Portfolio page, keep short-selling toggle off, click Optimise if needed.

Script:

"Now we compute the optimal portfolio. The utility function is U equals expected return minus A over two times portfolio variance. The optimiser chooses the weights that maximise this utility."

"First, we use the long-only case, which is the more practical setting for most retail investors. The constraints are that the weights must sum to one, and each weight must be between zero and one."

"For the sample Conservative investor with A equals 5.94, the long-only optimal portfolio has expected return of about 18.90 percent, volatility of 13.55 percent, and utility of 0.134444. The displayed Sharpe ratio is now computed as expected return minus the MAS 1-year T-bill yield, divided by volatility."

"The allocation is approximately 71.55 percent Eastspring Japan Dynamic, 23.71 percent Amova Singapore Equity, and 4.74 percent BlackRock World Gold."

"This result is concentrated because the optimiser is using historical sample returns and covariance. Japan Dynamic had the strongest risk-adjusted performance in the sample, while Singapore Equity and Gold help improve diversification. This is why we also show the sensitivity analysis, so users can see how the allocation changes when A changes."

## 12:30-13:45 - Optimal Portfolio With Shorting Allowed

Visual: Toggle "Allow short selling" and optimise again.

Script:

"Next, we allow short selling. In this setting, weights are unrestricted except that the net sum must equal one. This demonstrates the theoretical model, but it also shows why constraints matter."

"For the same A equals 5.94, the short-allowed optimal portfolio has expected return of about 75.91 percent and volatility of 35.16 percent. It includes large long exposures to Singapore Equity, Global Technology, Japan Dynamic, Gold, and Energy, and short positions in AI, Global Dividend, US, ASEAN, and Emerging Markets."

"These weights are leveraged: some positions are above 100 percent and some are negative. The model is mathematically valid under the unconstrained short-selling assumption, but in practice a retail platform would normally add leverage limits, margin costs, borrowing costs, and product suitability checks."

"Therefore, the long-only result is the more realistic recommendation, while the short-allowed result is useful for demonstrating the impact of relaxing constraints."

## 13:45-14:30 - Sensitivity Analysis and User Experience

Visual: Scroll to sensitivity analysis chart and frontier overlay.

Script:

"The Portfolio page also includes a frontier overlay, showing where the optimal portfolio sits relative to individual funds and the efficient frontier. The sensitivity analysis shows how allocations shift when A changes around the investor's value."

"This is important because it makes the model explainable. A user can see not only the final recommendation, but also how the recommendation responds to a more conservative or more aggressive risk setting."

"The app also includes a language and theme control in the top bar, and state is maintained across the workflow so that loaded funds and risk-profile results carry forward into the final portfolio page."

## 14:30-15:00 - Closing

Visual: Return to Portfolio page metrics or final slide.

Script:

"In summary, our project satisfies the main requirements of the BMD5302 robot adviser assignment. We selected ten FSMOne fund products, calculated expected returns and the covariance matrix, visualised efficient frontiers with and without short sales, identified the GMVP, built a questionnaire-based risk-aversion model, and implemented a working web platform that recommends a personalised optimal portfolio."

"The main limitation is that the model relies on historical return and covariance estimates, and the short-allowed version does not include real-world trading constraints. Future improvements could include transaction costs, leverage limits, rolling-window estimates, and more robust suitability controls. The risk-free-rate fetch is network dependent, so the app reports fallback metadata and uses zero only if MAS data is unavailable."

"Thank you for watching our demonstration."
