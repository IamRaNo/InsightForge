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

