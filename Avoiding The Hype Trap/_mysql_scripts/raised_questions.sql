SELECT * FROM ipo LIMIT 5;

SELECT * FROM prices LIMIT 5;

/* ===============
Questions Rased from Univariate Analysis of Python
=============== */

/* Companies with final price more than 1115 */
SELECT * FROM ipo WHERE final_price > 1115;

/* Companies with price change more than 85% on first day */
SELECT * FROM ipo WHERE price_change > 85;

/* Companies with retail subscription more than 60% */
SELECT * FROM ipo WHERE retail_subscription > 60;

/* Companies with 1 week return more than 90% */
SELECT * FROM ipo WHERE ret_1w > 90;

/* Companies with 1 month return more than 110% */
SELECT * FROM ipo WHERE ret_1m > 110;

/* Companies with 3 month return more than 112% */
SELECT * FROM ipo WHERE ret_3m > 112;

/* Companies with 6 month return more than 150% */
SELECT * FROM ipo WHERE ret_6m > 150;

/* Companies with 1 year return more than 180% */
SELECT * FROM ipo WHERE ret_1y > 180;

/* Companies with volatility more than 5.6 */
SELECT * FROM ipo WHERE volatility > 5.6;