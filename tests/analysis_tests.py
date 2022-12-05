def test_value_at_risk_chart():
    p_str = f"{str(Path(__file__).parents[1])}/test_portfolio.csv"
    start = dt.datetime(2022, 6, 1).date()
    end = dt.datetime.today().date()
    p = test_portfolio(p_str)
    var = calculate_VaR(start_date="2022-09-12", end_date="2022-11-12", portfolio=p)
    VaR_Chart(var).create_chart().show()


def test_satefy_first_ratio_chart():
    sfr = calculate_SFR(p, exp_return=0.02, start_date=start, end_date=end)
    SFR_Chart(sfr).create_chart().show()
