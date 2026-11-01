# Forgejo recovery drill runbook

This is a procedure for a customer-authorized, isolated restore rehearsal. It is not an automated feature of this repository, and it has not yet been exercised against a customer backup. A passing archive inventory or Restorable recipe is not a successful application restore.

Forgejo stores state across its database, repositories, configuration, and storage; a consistent backup can require stopping the service. The exact restore depends on the deployment's database, paths, object storage, and queue configuration. See the [official backup and restore guide](https://forgejo.org/docs/v17.0/admin/setup/backup/) before each drill.

## 1. Agree on scope

Before receiving or accessing backup data, record the customer's written authorization, selected snapshot or dump, Forgejo version, database type, deployment layout, expected recovery point, and named operator. List external dependencies from `app.ini` (for example S3-compatible storage, Redis, or external search). Agree which checks can be performed without contacting production systems.

Use a customer-controlled environment where possible. Do not upload backups or reports to this project's services: this project has no hosted service. Treat backups as production data because they can contain source code, account data, and encryption keys.

## 2. Prepare an isolated target

- Use a disposable VM or sandbox with access limited to the drill operator.
- Keep it off production networks and block outbound traffic by default. In particular, prevent email delivery, webhooks, mirrors, OAuth callbacks, and Actions runners from reaching real systems.
- Do not reuse production credentials or point the sandbox at production databases, Redis, object storage, DNS, or SMTP.
- Match the Forgejo version and database engine used by the selected backup where practical. Record any mismatch.
- Start with an empty restore target. Never restore into a production data directory. Never use destructive restore options against a live target.

If isolation cannot be demonstrated, stop before restoring or starting Forgejo.

## 3. Restore and run the available checks

For a Restic snapshot, select the agreed snapshot and restore it into the disposable target using the customer's configured Restic workflow. Restic documents that restore writes into a target directory; its `--delete` option can remove files from that target, so this runbook does not require or recommend it. See the [Restic restore documentation](https://github.com/restic/restic/blob/master/doc/050_restore.rst).

For the default `WORK_PATH` plus local SQLite layout, run the [Forgejo Restorable recipe](../integrations/restorable/forgejo.yaml) against that snapshot. It checks the expected config and database paths, samples restored file checksums, and runs SQLite integrity validation. It does not verify custom layouts, PostgreSQL, external object storage, full application startup, or semantic correctness of issues and repositories.

For a native Forgejo dump, use the local inventory CLI first:

```sh
python3 forgejo_recovery_check.py /path/to/forgejo-dump.zip --verify-integrity
```

Review the archive findings against the instance's actual configuration. A candidate filename is not proof of a complete or consistent restore. Do not treat unsupported CRC checks as a pass.

## 4. Verify application behavior only when authorized

Only continue if the customer explicitly authorized a full startup check and the isolation controls above are active. Work on a disposable copy because Forgejo startup can change database state during migrations. Restore the database and files using the customer's documented procedure, provide a sandbox-only configuration, and start the matching Forgejo binary.

Record only agreed checks, such as:

- Forgejo starts and an administrator can sign in using a temporary sandbox account.
- A customer-selected repository can be cloned and its expected reference or commit ID matches a value the customer supplied for the drill.
- Agreed issue or pull request records are visible, without exporting their contents.
- Local storage is readable. For external storage or services, verify only against customer-provided isolated test resources.
- SSH access works if the drill includes the built-in SSH server and its host keys.

Do not trigger real Actions workflows, outbound webhooks, email, mirrors, or OAuth integrations. Do not test credentials by sending data to external services.

## 5. Report and clean up

Give the customer a private report containing the snapshot identifier/recovery point, target RTO/RPO if the customer has defined them, tested Forgejo/database versions, deployment assumptions, checks performed, pass/fail/unknown results, end-to-end elapsed time, any manual fixes, and uncovered dependencies. Record target and observed values separately; a drill does not create a contractual recovery objective. Do not include backup contents, secrets, repository names, user data, or raw `app.ini` values. Mark a check `unknown` when it was not authorized or could not be isolated.

After the customer confirms the report is retained, destroy the disposable VM, restored volumes, temporary credentials, and working copies according to the customer's retention policy. Record what was destroyed. If cleanup cannot be verified, disclose that in the report.

## Drill outcome

A drill passes only when the agreed restore completed in the isolated target and each required check passed. An inventory-only check, recipe-only check, or partially authorized run is a limited result, not proof of full Forgejo recoverability. The report should state the gap and next corrective action without claiming certification.
