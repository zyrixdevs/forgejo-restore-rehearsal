# Market research

Research date: 2026-11-01. Desk research only; no user interviews or purchase evidence.

## Problem evidence

Forgejo says it does not provide or recommend one backup tool. Even the simplest setup stores repositories and bulk files on disk and user interaction data in SQL, and a consistent backup while Forgejo is running is not trivial. Restoring requires coordinating the database, files, configuration, and startup. Its guide identifies `[security].SECRET_KEY` as essential to decrypt stored webhook, Actions, mirror, and two-factor credentials; losing the OAuth JWT secret can require integrations to reauthenticate. [Official Forgejo guide](https://forgejo.org/docs/v17.0/admin/setup/backup/)

Forgejo's documented `dump` command creates an archive and exposes flags to skip repositories, LFS, attachments, packages, index data, and repository archives. The official CLI guide does not describe a whole-instance restore subcommand; the recovery guide explains a manual sequence. This makes an operator-facing dump inventory a concrete first tool, although it still cannot prove a successful restore. [Forgejo CLI reference](https://forgejo.org/docs/v17.0/admin/command-line/)

Forgejo can store each subsystem locally or in S3-compatible MinIO, with global defaults and per-subsystem overrides. A dump archive cannot prove that an external bucket was backed up; the included `app.ini` can at least identify these configured external components for operator follow-up. [Forgejo storage guide](https://forgejo.org/docs/v17.0/admin/setup/storage/)

The recovery guide also calls for preserving host keys when Forgejo's built-in SSH server is enabled, because clients can reject the host after recovery if its key changes. The config reference lists the key-pair paths under `[server].SSH_SERVER_HOST_KEYS`; the prototype now reports filename candidates when `[server].START_SSH_SERVER` is enabled. It cannot prove that the key is the correct one or that a custom data path was mapped correctly. [Forgejo recovery guide](https://forgejo.org/docs/v17.0/admin/setup/backup/) · [config reference](https://forgejo.org/docs/v17.0/admin/config-cheat-sheet/)

The same recovery guide says Redis-backed queues and Elasticsearch/Meilisearch indexers need separate backup handling, while `channel` and `dummy` queues cannot be backed up. The CLI now surfaces these configuration values for follow-up; it does not inspect Redis or search-service backups. [Forgejo recovery guide](https://forgejo.org/docs/v17.0/admin/setup/backup/)

These facts establish operational complexity, not buyer demand.

## Adjacent alternatives

Generic app-aware restore verification is already a product category. [Restorable](https://restorable.dev/) requires an existing Restic repository and documents real restores in disposable sandboxes, app-aware checks, and recipes for Nextcloud, Vaultwarden, and Immich. Its public docs do not list a Forgejo recipe. It is not a direct drop-in checker for a raw `forgejo dump` ZIP, although operators may be able to build a workflow around it. [RestoreProof](https://restoreproof.io/) accepts several backup sources and advertises file archive checks, but its public templates do not list Forgejo. This creates a narrow native-dump inspection wedge; it does not yet establish a defensible advantage or willingness to pay.

RestoreProof currently lists €49/month and €249/month plans, including scheduled runs and report history; Restorable describes its cloud dashboard as free during open beta and lists an $8/month Pro plan. These prices show adjacent category pricing, not Forgejo demand, sales, or a viable price for this product.

A [Forgejo community thread](https://www.reddit.com/r/forgejo/comments/1o9e16d) asks for a quick check that the `forgejo dump` ZIP is not corrupted and contains expected data such as LFS or SQLite. A separate DevOps discussion reports months of nightly dumps with a database but no repository directory. More specifically, a self-hosting operator made automated restore verification a blocker for migrating issue/PR metadata into Forgejo until the offsite copy could be restored from a clean machine; their issue later records successful sample-file recovery from Backblaze B2 but a remaining break-glass restore drill. This is one operator's issue tracker, not market-size or purchase evidence. [DevOps discussion](https://www.reddit.com/r/devops/comments/1vz9wis/how_much_maintenance_to_manage_a_forgejo/) · [homelab issue #174](https://github.com/cwage/homelab/issues/174)

A recent DevOps discussion about restore testing includes a founder's informal poll summary: respondents described automated tests, manual compliance-driven checks, and no regular schedule. The post also promotes that founder's restore-verification service, so it is biased and the sample size/method are unclear. It is a clue that scheduled recovery evidence is discussed, not proof that Forgejo operators will pay. [Discussion](https://www.reddit.com/r/devops/comments/1wln0gf/do_you_really_test_your_backup/)

There are capable do-it-yourself substitutes. A public Forgejo/Traefik deployment repository runs CI that boots its own stack, creates and pushes a real repository, then exercises backup/restore scenarios and verifies the commit survived. This proves a deployment-specific end-to-end check is practical; its documented script is coupled to that stack and warns to run against staging because it stops Forgejo and empties the data directory. A homelab operator separately built recurring offsite sample restores. A viable gap would need to make isolated, non-destructive recovery checks reusable across existing Forgejo installs and native dumps, with evidence an MSP can hand to a customer. Even that overlaps general restore platforms and needs validation. [Deployment verification workflow](https://github.com/heyvaldemar/forgejo-traefik-letsencrypt-docker-compose/blob/main/README.md#testing) · [homelab restore issue](https://github.com/cwage/homelab/issues/174)

The current prototype offers an opt-in ZIP CRC scan, itemized component inventory, and operator-selected requirements, but still does not run a restore. These features are a preflight/lead-in, not a paid product by themselves.

## Hypothesis to validate

Keep the preflight and Restorable recipe free. The paid hypothesis is setup/support and supervised restore drills for MSPs managing multiple Forgejo instances, using an isolated Restorable run and customer-ready evidence. Sell per drill initially; no price is justified yet. A standalone runner is worth building only if interviews find Forgejo-specific checks the generic engine cannot handle. Before expanding into hosted scheduling, seek five operator interviews, two supervised pilots, and one explicit paid-pilot commitment. These are proposed gates, not achievements.

## Risks and unknowns

- No Forgejo-specific willingness-to-pay signal found yet.
- Existing backup scripts and generic restore-verification products may be sufficient.
- A capable public Forgejo deployment repository already has CI-based end-to-end restore checks; a Forgejo-themed wrapper would not be a defensible product.
- RestoreProof's promoted product has a wider feature set and is closer to the paid hypothesis than the current CLI; compatibility/integration may be a better route than competing as another platform.
- Adjacent vendors already have pricing and broad product coverage; the local preflight alone has no clear paid differentiation.
- Archive layouts are operator-specific; heuristics can produce false positives and false negatives.
- A preflight cannot prove a successful application restore; only an isolated end-to-end rehearsal can.
- Restore environments may contain sensitive source code, secrets, and personal data; no hosted handling is planned.
