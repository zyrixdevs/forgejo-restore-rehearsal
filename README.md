# Forgejo Restore Rehearsal

An open-source, local-first tool for checking whether a Forgejo backup set contains the recovery components its operator expects.

Forgejo stores state across a database, Git repositories, files, and configuration. Some configuration secrets are required to decrypt credentials after recovery. Forgejo's built-in `dump` command can skip repositories and several data types; this project aims to make obvious omissions visible before an outage. It does not connect to Forgejo, upload data, restore the server, or certify a backup.

## Status

Early prototype. The product hypothesis is that small teams and MSPs running Forgejo want an easier, repeatable way to rehearse recovery and retain evidence. This has not been validated with customers, and no revenue exists.

## First milestone

Build a local preflight that inspects backup archive inventories without extracting or executing them, highlights missing database/repository/storage/config pieces, and saves a redacted report. A later milestone may run a restore in an isolated disposable environment; it must never target production.

## Why this problem

Forgejo's administrator guide says backups span multiple data locations and restoring requires coordinating database, files, configuration, and startup. The guide also calls out unique encryption and OAuth secrets that can break stored credentials if they are lost. [Forgejo backup and restore guide](https://forgejo.org/docs/v17.0/admin/setup/backup/)

## Safety and scope

- Runs against backup files chosen by the operator; no service login or external upload.
- Does not extract untrusted archives in the preflight milestone.
- Does not print configuration values or secret material.
- A complete-looking archive is not proof that it can be restored.
- No automated restore, hosted service, pricing, or sales claims yet.

## Business hypothesis

Keep the recovery runner open source. If discovery confirms a recurring pain, test paid supervised recovery drills and evidence reports for organizations operating Forgejo. Generic restore assurance is competitive, Forgejo-specific willingness to pay is unknown, and this is only a hypothesis.

## Development

The preflight inventories archive names and reads up to 1 MiB from `app.ini` to check whether the two documented secret settings are configured. It recognizes likely database, repository, and storage entries and reports whether the core candidates appear present. It does not extract archives or print setting values. If no inspectable `app.ini` is found, secret checks are reported as unknown (`null`), not missing.

```sh
python3 forgejo_recovery_check.py backup.tar.gz database.sql.gz --report recovery-report.json
```

Optional storage categories can be required explicitly when the operator expects them in the archive. For ZIP dumps, optionally verify every entry's CRC (this reads the complete uncompressed archive and can take time):

```sh
python3 forgejo_recovery_check.py forgejo-dump.zip --verify-integrity
python3 forgejo_recovery_check.py forgejo-dump.zip --require-component lfs --require-component attachments
```

This checks ZIP entry integrity only; it does not prove database consistency or a successful application restore. Other archive formats report the CRC check as unsupported. The command exits nonzero if a core component candidate is missing or a requested CRC check fails or is unsupported.

The report lists likely presence for attachments, LFS, avatars, repository avatars/archives, packages, Actions data, and custom files. Required optional components must be chosen by the operator; the tool does not infer external object storage from `app.ini`. Custom storage and repository paths, external secret files, database validity, consistency, and application behavior are not verified. Read [`docs/MARKET_RESEARCH.md`](docs/MARKET_RESEARCH.md) before treating this as a product direction.

## License

MIT. See [LICENSE](LICENSE).
