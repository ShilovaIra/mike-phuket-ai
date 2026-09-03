# Partner Dashboard is a separate site on the existing API process

Partner Users are not Operators and must not see Operator CRUD or bot-wide stats. We give them their own site (own URL, own login). Partner auth and stats live in their own Python package, mounted on the existing admin-api process; Partner User tokens cannot call Operator routes.

We rejected extra routes on the Operator admin site (wrong audience, easy to leak). We rejected a fourth Docker API service — a read-mostly stats page does not earn another container; one database and one backend deploy stay simpler.
