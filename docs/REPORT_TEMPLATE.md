# Forgejo Recovery Evidence Report

Copy this template to customer-controlled storage for each authorized review. Do not publish or commit a completed report. Keep backup identifiers and notes only as detailed as the customer has approved; never include secrets, repository names, user data, raw configuration values, or backup contents.

## Review record

- Report ID: `[customer-generated non-sensitive ID]`
- Review date (UTC): `[YYYY-MM-DD]`
- Reviewer: `[role or approved name]`
- Customer-approved scope reference: `[internal reference; no customer URL]`
- Result level: `[inventory only | component checks | isolated Forgejo startup | application checks]`

## Recovery point and environment

- Backup/snapshot reference: `[customer-approved identifier or redacted]`
- Recovery point timestamp: `[if known]`
- Target Forgejo version: `[version]`
- Observed backup Forgejo version: `[version | unknown]`
- Database type configured in archived `app.ini`: `[mysql/postgres/sqlite3/unset/mixed/unknown]`
- Effective database engine/version observed in the restored instance: `[engine/version | unknown]`
- Restore environment: `[customer-controlled isolated environment description]`
- Isolation and outbound-network controls confirmed: `[yes/no/unknown; explain briefly]`
- External dependencies in scope: `[service categories only, no endpoints or credentials]`

## Recovery objectives and timing

| Measure | Customer target | Observed | Notes |
|---|---|---|---|
| Recovery time (RTO) | `[if defined]` | `[elapsed or unknown]` | `[start/end events]` |
| Recovery point (RPO) | `[if defined]` | `[timestamp or unknown]` | `[selected recovery point]` |

Targets are customer-provided planning values. Observed results apply only to this drill and do not create a service guarantee or contractual objective.

## Checks

| Check | Result (`pass` / `fail` / `unknown` / `not authorized`) | Evidence reference kept by customer | Notes or manual fixes |
|---|---|---|---|
| Archive integrity (if supported and requested) |  |  |  |
| Database candidate or integrity check |  |  |  |
| Configuration and required secrets available |  |  |  |
| Repository data |  |  |  |
| Required storage components |  |  |  |
| External dependencies |  |  |  |
| Forgejo startup |  |  |  |
| Customer-approved application checks |  |  |  |
| Cleanup verified |  |  |  |

Evidence references must point to customer-controlled records. Do not paste screenshots, logs, paths, repository names, user data, or secret values into this report unless separately authorized and protected.

## Findings and limitations

- Missing or unverified recovery components: `[summary]`
- Manual fixes required: `[summary or none]`
- Checks not performed and why: `[summary or none]`
- Tool/recipe versions and configuration assumptions: `[versions and non-secret assumptions]`
- Limitations: `[for example custom paths, PostgreSQL, external storage, or full application semantics not covered]`

## Outcome and next action

- Outcome: `[pass for agreed scope | limited result | failed]`
- Next corrective action: `[owner role and action; no personal contact data]`
- Customer confirmation of report retention and cleanup: `[date/status]`

A pass applies only to the checks agreed for this review. An inventory-only or recipe-only result is not proof that a full Forgejo instance can be recovered.
