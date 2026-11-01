# Forgejo Restore Rehearsal

An open-source, local-first tool for checking whether a native Forgejo dump contains the recovery components its operator expects.

Forgejo stores state across a database, Git repositories, files, and configuration. Some configuration secrets are required to decrypt credentials after recovery. Forgejo's built-in `dump` command can skip repositories and several data types; this project aims to make obvious omissions visible before an outage. It does not connect to Forgejo, upload data, restore the server, or certify a backup.

## Status

Early prototype. The product hypothesis is that small teams and MSPs running Forgejo want an easier, repeatable way to rehearse recovery and retain evidence. This has not been validated with customers, and no revenue exists.

## Current MVP

The local CLI inventories backup archives without extracting or executing them, highlights missing database/repository/storage/config candidates, optionally checks ZIP entry CRCs, and saves a redacted report with a UTC timestamp and schema version. A later milestone may run a restore in an isolated disposable environment; it must never target production.

## Why this problem

Forgejo's administrator guide says backups span multiple data locations and restoring requires coordinating database, files, configuration, and startup. The guide also calls out unique encryption and OAuth secrets that can break stored credentials if they are lost. [Forgejo backup and restore guide](https://forgejo.org/docs/v17.0/admin/setup/backup/)

An operator in a public DevOps discussion reported discovering that months of nightly Forgejo dumps contained the database but not the repositories. This tool's required-component checks target that class of omission; one report does not establish broad demand. [Discussion](https://www.reddit.com/r/devops/comments/1vz9wis/how_much_maintenance_to_manage_a_forgejo/)

## Safety and scope

- Runs against backup files chosen by the operator; no service login or external upload.
- Does not extract untrusted archives in the preflight milestone.
- Does not print configuration values or secret material.
- A complete-looking archive is not proof that it can be restored.
- No automated restore or hosted service yet.

## Business hypothesis

Keep the native-dump checker and Restorable recipes open source. Managed Forgejo services already bundle backups, and enterprise providers advertise restore-testing help. The narrow paid hypothesis is a provider-independent, customer-controlled Forgejo restore drill with private evidence for self-hosted teams/MSPs whose current backup arrangement does not test application recovery. Charge per drill only if discovery confirms that gap. No price, buyer demand, or sales are validated; see [`docs/MARKET_RESEARCH.md`](docs/MARKET_RESEARCH.md).

## Development

Install the current source directly with [`pipx`](https://pipx.pypa.io/):

```sh
pipx install git+https://github.com/zyrixdevs/forgejo-restore-rehearsal.git
forgejo-recovery-check --help
```

The CLI uses only the Python standard library. This installs the current repository version; it is not a versioned PyPI release.

The preflight inventories archive names and reads up to 1 MiB from `app.ini` to check whether the two documented secret settings are configured. It distinguishes SQLite files from SQL dumps, recognizes repository and storage entries, and reports whether core candidates appear present. It does not extract archives or print setting values. If no inspectable `app.ini` is found, secret checks are reported as unknown (`null`), not missing.

```sh
python3 forgejo_recovery_check.py backup.tar.gz database.sql.gz --report recovery-report.json
```

Optional storage categories can be required explicitly when the operator expects them in the archive. For ZIP dumps, optionally verify every entry's CRC (this reads the complete uncompressed archive and can take time):

```sh
python3 forgejo_recovery_check.py forgejo-dump.zip --verify-integrity
python3 forgejo_recovery_check.py forgejo-dump.zip --require-component lfs --require-component attachments
```

This checks ZIP entry integrity only; it does not prove database consistency or a successful application restore. Other archive formats report the CRC check as unsupported. The command exits nonzero if a core component candidate is missing or a requested CRC check fails or is unsupported. If the instance legitimately has no repositories, `--allow-empty-repositories` waives only that candidate check and records the waiver in the report.

The report lists likely presence for attachments, LFS, avatars, repository avatars/archives, packages, Actions data, and custom files. It also reads `STORAGE_TYPE` values from `app.ini` and identifies components configured for MinIO/S3; it cannot verify that the external object store was backed up. When Forgejo's built-in SSH server is enabled, it reports whether the configured host-key filenames appear in the archive. It flags Redis queues and external search indexers for separate recovery planning. These are configuration-derived warnings, not proof the dependencies were backed up. Required optional components must be chosen by the operator. Custom local paths, external secret files, database validity, consistency, and application behavior are not verified. Read [`docs/MARKET_RESEARCH.md`](docs/MARKET_RESEARCH.md) before treating this as a product direction.

Archive entries with absolute paths or parent-directory traversal are excluded from recovery-candidate checks and counted in `unsafe_archive_paths_ignored`; they are never extracted.

## Restic restore checks

For Restic snapshots with the default local SQLite database, [`integrations/restorable/forgejo.yaml`](integrations/restorable/forgejo.yaml) checks Forgejo's default `WORK_PATH` paths and runs SQLite integrity validation. For a snapshot that also contains an exported PostgreSQL dump, [`integrations/restorable/forgejo-postgres.yaml`](integrations/restorable/forgejo-postgres.yaml) loads it into Restorable's throwaway PostgreSQL container. Edit the paths in either recipe to match your snapshot, then copy the selected recipe into the directory referenced by Restorable's `agent.yaml` `recipes` setting. Neither recipe starts Forgejo or checks external object storage. See [Restorable's recipe guide](https://github.com/restorable-dev/restorable#check-types).

For a customer-authorized, manually supervised full restore rehearsal, see the [recovery drill runbook](docs/RESTORE_DRILL.md). The procedure is not automated or yet validated against a real Forgejo backup.

## License

MIT. See [LICENSE](LICENSE).
