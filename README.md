# Factor risk

Synthetic 30-name panel for a portfolio-risk screen. Not Barra, Axioma or Bloomberg. Not live prices.

`factor_risk.py` fits a market, value and momentum model, a three-component statistical model, a long-only low-beta book, and held-out VaR, stress, Sharpe and drawdown. `STUDY.md` is the note to read before an interview.

## Result

| Book | Ann. vol | Factor share | Market exposure |
|---|---:|---:|---:|
| Equal weight | 15.4% | 95% | 1.02 |
| Low beta, 8% name cap | 13.1% | 83% | 0.79 |

Statistical model, same equal-weight book: 15.8% vol. First three components explain 49% of panel variance.

Held-out low-beta book: daily vol 0.91%, historical 95% VaR 1.57%, max drawdown −20%, Sharpe −2.6. The Sharpe is the seed, not a strategy. A −3 sd market shock and a −2 sd value shock costs 2.3%, specific risk excluded.

A market exposure of 0.4 is not feasible long-only. The cheapest names still have betas near 0.6.

## Run

```bash
pip install -r requirements.txt
python factor_risk.py
```
