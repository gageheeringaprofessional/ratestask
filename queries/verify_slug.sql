-- verify a code exists
SELECT EXISTS(
	SELECT 1
	FROM regions
	WHERE slug = %(target)s
)