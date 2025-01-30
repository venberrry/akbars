SELECT
    t1.report_dt,
    t1.contract_num,
    t1.currency,
    t1.balance,
    t2.currency_dt,
    t2.currency,
    t1.balance * t2.currency AS balance_in_rub
FROM table1 AS t1
JOIN
    table2 AS t2
    ON t1.currency = t2.currency
    AND t2.currency_dt = (
        SELECT MIN(currency_dt)
        FROM table2
        WHERE currency = t1.currency
        AND currency_dt > t1.report_dt
    )
ORDER BY
    t1.report_dt, t1.contract_num;
