-- verify a slug exists
SELECT EXISTS(
	SELECT 1
	FROM regions
	WHERE slug = %(location)s
)