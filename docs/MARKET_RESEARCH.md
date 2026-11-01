# Market research

Research date: 2026-11-01. Desk research only; no user interviews or purchase evidence.

## Problem evidence

Forgejo says it does not provide or recommend one backup tool. Even the simplest setup stores repositories and bulk files on disk and user interaction data in SQL, and a consistent backup while Forgejo is running is not trivial. Restoring requires coordinating the database, files, configuration, and startup. Its guide identifies `[security].SECRET_KEY` as essential to decrypt stored webhook, Actions, mirror, and two-factor credentials; losing the OAuth JWT secret can require integrations to reauthenticate. [Official Forgejo guide](https://forgejo.org/docs/v17.0/admin/setup/backup/)

Forgejo's documented `dump` command creates an archive and exposes flags to skip repositories, LFS, attachments, packages, index data, and repository archives. The official CLI guide does not describe a whole-instance restore subcommand; the recovery guide explains a manual sequence. This makes an operator-facing dump inventory a concrete first tool, although it still cannot prove a successful restore. [Forgejo CLI reference](https://forgejo.org/docs/v17.0/admin/command-line/)

These facts establish operational complexity, not buyer demand.

## Adjacent alternatives

Generic app-aware restore verification is already a product category. [Restorable](https://restorable.dev/) documents real restores in disposable sandboxes, app-aware checks, and recipes for Nextcloud, Vaultwarden, and Immich. [RestoreProof](https://restoreproof.io/) markets disposable restore checks and reports for databases and applications. This overlaps the core promise; Forgejo-specific demand and a distinct advantage are not established.

RestoreProof currently lists €49/month and €249/month plans, including scheduled runs and report history; Restorable describes its cloud dashboard as free during open beta and lists an $8/month Pro plan. These prices show adjacent category pricing, not Forgejo demand, sales, or a viable price for this product.

A [Forgejo community thread](https://www.reddit.com/r/forgejo/comments/1o9e16d) asks for a quick check that the `forgejo dump` ZIP is not corrupted and contains expected data such as LFS or SQLite. This is one operator's question, not evidence of broad demand or buying intent. The current prototype now offers an opt-in ZIP CRC scan and component inventory, but still does not run a restore.

## Hypothesis to validate

Offer a free local recovery preflight and rehearsal runner. If organizations repeatedly need help proving Forgejo recoverability, test a paid supervised drill and evidence report. Before building hosted scheduling or restore orchestration, seek five operator interviews, two supervised pilots, and one explicit paid-pilot commitment. These are proposed gates, not achievements.

## Risks and unknowns

- No Forgejo-specific willingness-to-pay signal found yet.
- Existing backup scripts and generic restore-verification products may be sufficient.
- Adjacent vendors already have pricing and broad product coverage; the local preflight alone has no clear paid differentiation.
- Archive layouts are operator-specific; heuristics can produce false positives and false negatives.
- A preflight cannot prove a successful application restore; only an isolated end-to-end rehearsal can.
- Restore environments may contain sensitive source code, secrets, and personal data; no hosted handling is planned.
