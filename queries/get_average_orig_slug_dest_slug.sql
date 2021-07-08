-- average price between origin and destination for each day
-- in date range where at least 3 transactions took place
SELECT txs.day,
	CASE WHEN day_counts.day_count >= 3 THEN AVG(txs.price)
		ELSE null
	END AS average
FROM (
	-- transactions (day, price) within relevant regions and date range
	SELECT day, price
	FROM prices
	WHERE orig_code IN %(origin)s
	AND dest_code IN %(destination)s
	AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
	GROUP BY day, price
	ORDER BY day ASC
) txs
LEFT JOIN (
	-- transaction count for each day within relevant regions and date range
	SELECT t.day, COUNT(*) as day_count
	FROM (
		-- transactions (day, price) within relevant regions and date range
		SELECT day, price
		FROM prices
		WHERE orig_code IN %(origin)s
		AND dest_code IN %(destination)s
		AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
		GROUP BY day, price
		ORDER BY day ASC
	) t
	GROUP BY day
	ORDER BY day ASC
) day_counts
ON txs.day = day_counts.day
GROUP BY txs.day, day_counts.day_count
ORDER BY txs.day ASC
;