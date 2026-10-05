# Factor risk: study note

Read this with `factor_risk.py` open. Every number below is what that script prints on seed 7. Synthetic data. Not Barra, not Axioma, not a live book.

The Millennium Portfolio Researcher seat in Mumbai asks for four things: a cash-equity factor model, a statistical factor model, tail risk (VaR and stress), and performance numbers (Sharpe, drawdown) plus an optimisation toolkit. This note is those four, in the order a reviewer will ask them.

## 1. Why a factor model exists

Thirty stocks, 378 days. A sample covariance is a 30 by 30 matrix, 465 unique numbers, estimated from a window that is not much longer than the cross-section. It is noisy, and it will tell you that two oil names moved together last year because of a residual, not because they share a factor.

A factor model forces the common part to be common. Each name is a set of exposures times a few factor returns, plus a residual that is its own.

$$
r_t = \alpha + B^{\top} f_t + \varepsilon_t
$$

$$
\Sigma = B^{\top} F B + D
$$

$f_t$ is the factor return on day $t$. $B$ is exposures by name. $F$ is the covariance of the factors. $D$ is diagonal: specific risk, the variance of $\varepsilon$. Off-diagonal specific covariance is set to zero. That is the modelling choice. If two names still move together after the factors, this model calls it noise.

Barra sells this object. $B$ there is fundamental: size, value, momentum, volatility, industry, country, maintained by the vendor. Axioma and Bloomberg PORT are the same product from other vendors. This script estimates $B$ by regression on three simulated factors. Same algebra. Different inputs. Say that distinction before anyone else does.

## 2. The known-factor fit

Factors are market, value and momentum. True betas were drawn, then returns were built as $B^{\top} f + \varepsilon$, then the true betas were thrown away. The fit does not see them.

Estimation window: first 378 business days. Design matrix is a column of ones plus the three factors. Ordinary least squares, one regression per name, which is what `lstsq` does on the whole panel at once.

The intercept is alpha. It is stored and not used. An alpha estimated in the same window as the beta is not a forecast. Using it in a mean-variance optimiser would be fitting the noise you just residualised. If asked why there is no expected-return model, that is the answer.

$D$ is the residual variance by name, sample variance with a degree-of-freedom correction. $F$ is the sample covariance of the three factor series in the same window. $\Sigma$ is then the formula above. Portfolio vol is $\sqrt{w^{\top} \Sigma w}$, annualised with $\sqrt{252}$.

## 3. What the equal-weight book says

Equal weight, $1/30$ each name.

| | |
|---|---|
| Annualised vol | 15.4% |
| Share of variance from the three factors | 95% |
| Exposure: market, value, momentum | 1.02, 0.02, −0.05 |

Ninety-five percent is the interview. The book is not risky because of the names. It is risky because every name carries the market. Value and momentum exposures net out across thirty random betas. A reviewer who asks "where is the risk" gets "the market factor" and then the table.

## 4. The statistical model

Same estimation window. Returns are demeaned. A singular-value decomposition gives the principal components. The first three right singular vectors are the loadings. Scores are returns times loadings. Specific risk is whatever the three components did not explain. Covariance is loadings, times the covariance of the scores, plus a diagonal residual. Same formula as the known-factor model. The factors are unnamed.

| | |
|---|---|
| Equal-weight vol, statistical | 15.8% |
| Equal-weight vol, known factors | 15.4% |
| Variance explained by the first three components | 49% (39%, 5%, 4%) |

The vols match. The stories do not. The known-factor model says the risk is market. The statistical model says the risk is the first component, which will be close to market in this simulation and will not be labelled. Forty-nine percent explained is not a failure. Equity panels have a large idiosyncratic share. A vendor model adds industries and countries to pick more of that up. Three components will not.

If asked which you would ship: the known-factor model, when you need to tell a portfolio manager that value drove the day. The statistical model, when you do not trust the factor definitions and you only need a covariance. Millennium's posting asks for both. This repo has both, on synthetic data.

## 5. The book construction, and the constraint that failed

The posting asks for an optimisation toolkit. The first attempt was a quadratic programme: minimise $w^{\top} \Sigma w$, long only, name cap 8%, market exposure at most 0.4. The solver returned without a feasible point.

That is the result, not a bug. True market betas were drawn from 0.6 to 1.4. A long-only book cannot have a market exposure below the lowest beta it is allowed to hold. With an 8% cap you must hold at least 13 names. The 13 lowest betas still average well above 0.4. The constraint was infeasible. Shipping a solver output that ignored that would have been worse than the failure.

The book in the script is the feasible version. Sort names by estimated market beta. Fill the book from the bottom, 8% each, until the weights sum to one. Thirteen names, nothing above the cap.

| | Equal weight | Low-beta book |
|---|---:|---:|
| Annualised vol | 15.4% | 13.1% |
| Factor share of variance | 95% | 83% |
| Market exposure | 1.02 | 0.79 |
| Value exposure | 0.02 | 0.09 |
| Momentum exposure | −0.05 | −0.11 |

Vol falls about two points. Factor share falls because the market piece shrank and specific risk, which was always there, is a larger fraction of a smaller total. Exposure did not reach 0.4. Say the sentence: a long-only book inherits the lowest beta you can actually hold.

Inverse-volatility weighting, tried in an earlier version, did almost nothing. It rescales names. It does not change the fact that every name has a market beta near one. Mention it only if asked. The low-beta book is the one that answers the question.

## 6. Tail risk and the performance numbers

All of these are on the last 126 days, which were not used to estimate $B$, $F$ or $D$. The low-beta weights are applied to that window.

| | |
|---|---|
| Daily vol | 0.91% |
| Historical 95% VaR | 1.57% |
| Max drawdown | −20.3% |
| Sharpe, annualised | −2.56 |
| Stress: market −3 sd, value −2 sd | −2.3% |

Historical VaR is the loss at the 5% quantile of daily portfolio returns, sign flipped. It is not a parametric VaR. A normal 95% VaR would be about 1.65 daily standard deviations, roughly 1.5% here. The historical number is close. On 126 days the 5% quantile is six days. Say the sample is short.

The stress is a factor shock, not a replay. Market return set to minus three estimation-window standard deviations, value to minus two, momentum unshocked. Portfolio loss is exposure times shock. Specific risk is not in that number. A name can gap for a reason that is not in $F$. The stress will not see it.

Sharpe is mean over standard deviation, times $\sqrt{252}$. It is −2.6 because the seed produced a falling held-out path. It is not a strategy result. Do not walk into the interview leading with it. If asked, say the sign is the simulation, and the object you would defend is the risk decomposition.

Drawdown is the worst peak-to-trough of the cumulative sum of daily returns. −20% on a 126-day window with a negative drift is ordinary. It is not a tail-risk finding.

## 7. What Barra does that this does not

Barra's $B$ is not a regression on a factor return you supply. Exposures are built from fundamentals and then standardised. Factor returns are estimated by cross-sectional regression each day. $F$ is a time-series covariance of those factor returns, with a weighting scheme and a correlation adjustment. Specific risk is a separate model, not the residual variance of one window. Industries and countries are in the factor set, so a sector bet shows up as a factor, not as specific risk.

Using Barra means loading a book and reading the exposure and the marginal contribution to risk. Building Barra means the vendor's research group. This repo is neither. It is the algebra in the middle.

## 8. Questions they will ask

Where is the risk in the equal-weight book. The market factor. Ninety-five percent of variance. Value and momentum net out.

Why did inverse vol fail and the low-beta book work. Inverse vol changes weights, not the common exposure. The low-beta book changes the exposure, down to 0.79, which is as far as a long-only 8% cap can go.

Why is 0.4 infeasible. Lowest betas start near 0.6, and the cap forces you to hold more than the single lowest name.

Why do the two vols match and the stories differ. Both covariances are factor-plus-diagonal. The statistical factors are unnamed. You cannot tell a portfolio manager that "component one" drove the day.

Why is alpha unused. Same-window alpha is not an expected return.

What is missing from the stress. Specific risk, and any factor you did not shock. Momentum was left at zero.

Is this Barra. No.

## 9. One minute

I fit a market, value and momentum model on a synthetic panel and a three-component statistical model on the same window. Equal-weight risk is 15.4%, almost all market. The statistical model gives 15.8% and does not name the factor. A long-only low-beta book cuts exposure from 1.02 to 0.79 and vol to 13.1%. A cap of 0.4 is infeasible. Held-out historical VaR is 1.6%. A market and value shock costs 2.3%, specific risk excluded. Not a vendor model.
