SELECT txs.day,
	CASE WHEN day_counts.day_count >= 3 THEN AVG(txs.price)
		ELSE null
	END AS average
FROM (
	-- transactions (day, price) within relevant regions and date range
	SELECT day, price
	FROM prices
	WHERE orig_code = %(origin)s
	AND dest_code = %(destination)s
	AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
	GROUP BY day, price
	ORDER BY day ASC
) txs
LEFT JOIN (
	-- transaction count for each day within relevant regions and date range
	SELECT tx_counts.day, COUNT(*) as day_count
	FROM (
		-- transactions (day, price) within relevant regions and date range
		SELECT day, price
		FROM prices
		WHERE orig_code = %(origin)s
		AND dest_code = %(destination)s
		AND day BETWEEN %(date_from)s::DATE AND %(date_to)s::DATE
		GROUP BY day, price
		ORDER BY day ASC
	) tx_counts
	GROUP BY day
	ORDER BY day ASC
) day_counts
ON txs.day = day_counts.day
GROUP BY txs.day, day_counts.day_count
;