#!/usr/bin/env python3
"""Inventory Forgejo backup archives without extracting their contents."""

import argparse
import configparser
import json
import sys
import tarfile
import zipfile
from pathlib import PurePosixPath


MAX_MEMBERS = 1_000_000
MAX_CONFIG_BYTES = 1_048_576
OPTIONAL_COMPONENTS = {
    "attachments": "attachments",
    "lfs": "lfs",
    "avatars": "avatars",
    "repository_avatars": "repo-avatars",
    "repository_archives": "repo-archive",
    "packages": "packages",
    "actions_logs": "actions_log",
    "actions_artifacts": "actions_artifacts",
    "custom": "custom",
}


def archive_members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_MEMBERS:
                raise ValueError(f"too many archive entries (limit {MAX_MEMBERS})")
            result = []
            for item in infos:
                config = None
                if PurePosixPath(item.filename.replace("\\", "/")).name.lower() == "app.ini" and item.file_size <= MAX_CONFIG_BYTES:
                    with archive.open(item) as stream:
                        config = stream.read(MAX_CONFIG_BYTES + 1)
                result.append((item.filename, item.file_size, config))
            return result
    with tarfile.open(path, "r:*") as archive:
        result = []
        member_count = 0
        for item in archive:
            if member_count >= MAX_MEMBERS:
                raise ValueError(f"too many archive entries (limit {MAX_MEMBERS})")
            member_count += 1
            if not (item.isfile() or item.isdir()):
                continue
            config = None
            if item.isfile() and PurePosixPath(item.name.replace("\\", "/")).name.lower() == "app.ini" and item.size <= MAX_CONFIG_BYTES:
                stream = archive.extractfile(item)
                if stream:
                    with stream:
                        config = stream.read(MAX_CONFIG_BYTES + 1)
            result.append((item.name, item.size, config))
        return result


def inspect(paths, verify_integrity=False, required_components=()):
    names = []
    config_files = []
    app_ini_found = False
    integrity_checks = []
    for path in paths:
        if verify_integrity:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as archive:
                    integrity_checks.append("failed" if archive.testzip() else "passed")
            else:
                integrity_checks.append("unsupported")
        else:
            integrity_checks.append("not_requested")
        members = archive_members(path)
        if len(names) + len(members) > MAX_MEMBERS:
            raise ValueError(f"too many archive entries across inputs (limit {MAX_MEMBERS})")
        for name, _size, config_bytes in members:
            normalized = str(PurePosixPath(name.replace("\\", "/"))).lower()
            names.append(normalized)
            app_ini_found |= PurePosixPath(normalized).name == "app.ini"
            if config_bytes is not None:
                if len(config_bytes) <= MAX_CONFIG_BYTES:
                    config_files.append(config_bytes)

    basenames = [PurePosixPath(name).name for name in names]
    database_candidates = {
        "sqlite_file": any(name in {"forgejo.db", "gitea.db"} or name.endswith(".sqlite3") for name in basenames),
        "sql_dump": any(name.endswith((".sql", ".sql.gz", ".dump")) for name in basenames),
    }
    database = any(database_candidates.values())
    repositories = any(
        part in {"repos", "forgejo-repositories"}
        for name in names for part in PurePosixPath(name).parts
    )
    optional_components = {
        component: any(path in PurePosixPath(name).parts for name in names)
        for component, path in OPTIONAL_COMPONENTS.items()
    }
    storage = any(optional_components.values())
    config = {"secret_key_configured": None, "oauth_jwt_secret_configured": None}
    if config_files:
        config["secret_key_configured"] = False
        config["oauth_jwt_secret_configured"] = False
    for config_bytes in config_files:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(config_bytes.decode("utf-8", errors="replace"))
        config["secret_key_configured"] |= bool(
            parser.get("security", "SECRET_KEY", fallback="").strip()
            or parser.get("security", "SECRET_KEY_URI", fallback="").strip()
        )
        config["oauth_jwt_secret_configured"] |= bool(
            parser.get("oauth2", "JWT_SECRET", fallback="").strip()
            or parser.get("oauth2", "JWT_SECRET_URI", fallback="").strip()
        )

    core_components = {
        "database": database,
        "app_ini": app_ini_found,
        "repository_data": repositories,
    }
    missing_required_components = [
        component for component in required_components if not optional_components[component]
    ]

    return {
        "archive_count": len(paths),
        "entry_count": len(names),
        "zip_crc_checks_in_input_order": integrity_checks,
        "core_components": core_components,
        "core_components_look_present": all(core_components.values()),
        "database_candidates": database_candidates,
        "optional_component_candidates": optional_components,
        "required_optional_components": list(required_components),
        "missing_required_optional_components": missing_required_components,
        "database_candidate_found": database,
        "repository_data_candidate_found": repositories,
        "common_storage_data_candidate_found": storage,
        "app_ini_found": app_ini_found,
        "app_ini_settings_inspected": bool(config_files),
        "secret_key_configured_in_app_ini": config["secret_key_configured"],
        "oauth_jwt_secret_configured_in_app_ini": config["oauth_jwt_secret_configured"],
        "limitations": [
            "Checks names and two app.ini settings only; it does not validate database contents, every configured path, or file integrity.",
            "Custom repository/storage paths and secrets stored in external files need operator review.",
            "A passing inventory is not a restore test or proof of recoverability.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", help="tar, tar.gz, tgz, or zip backup archives")
    parser.add_argument("--report", help="write JSON report to a new file (default: stdout)")
    parser.add_argument("--verify-integrity", action="store_true", help="read each ZIP entry and verify its CRC; other formats are reported unsupported")
    parser.add_argument("--require-component", action="append", choices=OPTIONAL_COMPONENTS, default=[], metavar="NAME", help="require an optional component; repeat for each (" + ", ".join(OPTIONAL_COMPONENTS) + ")")
    args = parser.parse_args()
    try:
        report = inspect(args.archives, args.verify_integrity, args.require_component)
        payload = json.dumps(report, indent=2) + "\n"
        if args.report:
            with open(args.report, "x", encoding="utf-8") as output:
                output.write(payload)
        else:
            sys.stdout.write(payload)
        if not report["core_components_look_present"]:
            return 1
        if report["missing_required_optional_components"]:
            return 1
        if args.verify_integrity and any(status != "passed" for status in report["zip_crc_checks_in_input_order"]):
            return 1
        return 0
    except (OSError, EOFError, RuntimeError, tarfile.TarError, zipfile.BadZipFile, ValueError, configparser.Error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
