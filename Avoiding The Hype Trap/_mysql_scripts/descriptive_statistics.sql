SELECT * FROM ipo LIMIT 5;

SELECT COUNT(DISTINCT company) FROM ipo;

SELECT MIN(listing_date) as first_date,MAX(listing_date) as last_date from ipo;


SELECT AVG(final_price) as average_price,
        MAX(final_price) as highest_price,
        MIN(final_price) as lowest_price
FROM ipo;

SELECT * FROM ipo WHERE final_price = 19;


SELECT AVG(price_change) as average_price,
        MAX(price_change) as highest_price,
        MIN(price_change) as lowest_price
FROM ipo;

SELECT * FROM ipo WHERE price_change = 267.18;

SELECT AVG(retail_subscription) as average_reatil_sub,
        MAX(retail_subscription) as highest_reatil_sub,
        MIN(retail_subscription) as lowest_reatil_sub
FROM ipo;

