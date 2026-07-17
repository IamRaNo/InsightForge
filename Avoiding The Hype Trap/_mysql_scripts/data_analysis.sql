SELECT * FROM ipo LIMIT 5;

--- Company with price change of 267%
SELECT * FROM ipo WHERE price_change > 250;

--- company with retail subscription of 360%
SELECT * FROM ipo WHERE retail_subscription > 350;

SELECT * FROM ipo WHERE ret_1w IS NULL;