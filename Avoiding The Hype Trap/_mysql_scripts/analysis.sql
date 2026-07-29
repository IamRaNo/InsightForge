SELECT * FROM ipo LIMIT 5;

/* ===============
Analytical Questions
/* ===============

/* is change of price have any difference over the time? */
SELECT 
    YEAR(listing_date) as listing_year,
    ROUND(AVG(price_change),2) as average_price_change
FROM ipo
GROUP BY YEAR(listing_date)
ORDER BY listing_year ASC;

/* is retail subscription have any difference over the time? */
SELECT 
    YEAR(listing_date) as listing_year,
    ROUND(AVG(retail_subscription),2) as average_retail_subscription
FROM ipo
GROUP BY YEAR(listing_date)
ORDER BY listing_year ASC;

/* is 1 Year return have any difference over the time? */
SELECT 
    YEAR(listing_date) as listing_year,
    ROUND(AVG(ret_1y),2) as average_return_1y
FROM ipo
GROUP BY YEAR(listing_date)
ORDER BY listing_year ASC;

/* is volatility have any difference over the time? */
SELECT 
    YEAR(listing_date) as listing_year,
    ROUND(AVG(volatility),2) as average_volatility
FROM ipo
GROUP BY YEAR(listing_date)
ORDER BY listing_year ASC;

/* dropdown have any difference over the time? */
SELECT 
    YEAR(listing_date) as listing_year,
    ROUND(AVG(max_drawdown),2) as average_max_drawdown
FROM ipo
GROUP BY YEAR(listing_date)
ORDER BY listing_year ASC;

/* Gain buckets over the years */
SELECT 
    YEAR(listing_date) as listing_year,
    gain_bucket as bucket,
    COUNT(*) as company_count
FROM ipo
GROUP BY listing_year,gain_bucket
ORDER BY company_count desc;


/* Gain buckets over the years */