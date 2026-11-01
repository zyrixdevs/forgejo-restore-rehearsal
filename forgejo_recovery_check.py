#!/usr/bin/env python3
"""Inventory Forgejo backup archives without extracting their contents."""

import argparse
import configparser
import json
import lzma
import stat
import sys
import tarfile
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath


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
STORAGE_SECTIONS = {
    "attachments": "attachment",
    "lfs": "lfs",
    "avatars": "avatar",
    "repository_avatars": "repo-avatar",
    "repository_archives": "repo-archive",
    "packages": "packages",
    "actions_logs": "storage.actions_log",
    "actions_artifacts": "actions.artifacts",
}
PATH_SETTINGS = {
    "server": ("APP_DATA_PATH",),
    "database": ("PATH",),
    "repository": ("ROOT",),
    "queue": ("DATADIR",),
    "indexer": ("ISSUE_INDEXER_PATH", "REPO_INDEXER_PATH"),
    **{section: ("PATH",) for section in STORAGE_SECTIONS.values()},
}


def safe_member_path(name):
    normalized = name.replace("\\", "/")
    posix_path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(normalized)
    return (
        not posix_path.is_absolute()
        and not windows_path.drive
        and ".." not in posix_path.parts
    )


def archive_members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_MEMBERS:
                raise ValueError(f"too many archive entries (limit {MAX_MEMBERS})")
            result = []
            for item in infos:
                mode = item.external_attr >> 16
                is_dir = item.is_dir() or stat.S_ISDIR(mode)
                file_type = stat.S_IFMT(mode)
                is_file = not is_dir and file_type in {0, stat.S_IFREG}
                if not (is_dir or is_file):
                    continue
                config = None
                if is_file and PurePosixPath(item.filename.replace("\\", "/")).name.lower() == "app.ini" and item.file_size <= MAX_CONFIG_BYTES:
                    with archive.open(item) as stream:
                        config = stream.read(MAX_CONFIG_BYTES + 1)
                result.append((item.filename, item.file_size, config, is_file))
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
            result.append((item.name, item.size, config, item.isfile()))
        return result


def inspect(paths, verify_integrity=False, required_components=(), allow_empty_repositories=False):
    names = []
    safe_names = []
    config_files = []
    file_names = []
    app_ini_found = False
    unsafe_archive_paths_ignored = 0
    integrity_checks = []
    per_archive_core_components = []
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
        archive_safe_names = []
        archive_file_names = []
        archive_app_ini_found = False
        for name, _size, config_bytes, is_file in members:
            normalized = str(PurePosixPath(name.replace("\\", "/"))).lower()
            names.append(normalized)
            is_safe_path = safe_member_path(name)
            if is_safe_path:
                safe_names.append(normalized)
                archive_safe_names.append(normalized)
            else:
                unsafe_archive_paths_ignored += 1
            if is_file and is_safe_path:
                file_names.append(normalized)
                archive_file_names.append(normalized)
                # ORIGINAL (preserved, not deleted — disabled by comment): app_ini_found |= PurePosixPath(normalized).name == "app.ini"
                if PurePosixPath(normalized).name == "app.ini":
                    app_ini_found = True
                    archive_app_ini_found = True
            if config_bytes is not None and is_safe_path:
                if len(config_bytes) <= MAX_CONFIG_BYTES:
                    config_files.append(config_bytes)
        archive_basenames = [PurePosixPath(name).name for name in archive_file_names]
        archive_has_database = any(
            name in {"forgejo.db", "gitea.db"} or name.endswith(".sqlite3")
            or name.endswith((".sql", ".sql.gz", ".dump"))
            for name in archive_basenames
        )
        archive_has_repositories = any(
            part in {"repos", "forgejo-repositories"}
            for name in archive_safe_names for part in PurePosixPath(name).parts
        )
        per_archive_core_components.append({
            "archive_index": len(per_archive_core_components) + 1,
            "core_components": {
                "database": archive_has_database,
                "app_ini": archive_app_ini_found,
                "repository_data": archive_has_repositories,
            },
        })

    basenames = [PurePosixPath(name).name for name in file_names]
    database_candidates = {
        "sqlite_file": any(name in {"forgejo.db", "gitea.db"} or name.endswith(".sqlite3") for name in basenames),
        "sql_dump": any(name.endswith((".sql", ".sql.gz", ".dump")) for name in basenames),
    }
    database = any(database_candidates.values())
    repositories = any(
        part in {"repos", "forgejo-repositories"}
        for name in safe_names for part in PurePosixPath(name).parts
    )
    optional_components = {
        component: any(path in PurePosixPath(name).parts for name in safe_names)
        for component, path in OPTIONAL_COMPONENTS.items()
    }
    storage = any(optional_components.values())
    config = {"secret_key_configured": None, "oauth_jwt_secret_configured": None}
    storage_types = {component: "unknown" for component in STORAGE_SECTIONS}
    ssh_enabled = None if not config_files else False
    ssh_host_key_names = set()
    external_dependencies = set()
    configured_path_settings = set()
    configured_database_types = set()
    if config_files:
        config["secret_key_configured"] = False
        config["oauth_jwt_secret_configured"] = False
    for config_bytes in config_files:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(config_bytes.decode("utf-8", errors="replace"))
        configured_database_types.add(
            parser.get("database", "DB_TYPE", fallback="").strip().lower() or "unset"
        )
        for section, options in PATH_SETTINGS.items():
            for option in options:
                if parser.has_option(section, option):
                    configured_path_settings.add(f"{section}.{option}".lower())
        config["secret_key_configured"] |= bool(
            parser.get("security", "SECRET_KEY", fallback="").strip()
            or parser.get("security", "SECRET_KEY_URI", fallback="").strip()
        )
        config["oauth_jwt_secret_configured"] |= bool(
            parser.get("oauth2", "JWT_SECRET", fallback="").strip()
            or parser.get("oauth2", "JWT_SECRET_URI", fallback="").strip()
        )
        if parser.getboolean("server", "START_SSH_SERVER", fallback=False):
            ssh_enabled = True
            host_keys = parser.get("server", "SSH_SERVER_HOST_KEYS", fallback="").strip() or "ssh/gitea.rsa, ssh/gogs.rsa"
            ssh_host_key_names.update(
                PurePosixPath(path.strip().replace("\\", "/")).name
                for path in host_keys.split(",") if path.strip()
            )
        queue_type = parser.get("queue", "TYPE", fallback="level").strip().lower()
        if queue_type == "redis":
            external_dependencies.add("queue:redis")
        elif queue_type in {"channel", "dummy"}:
            external_dependencies.add("queue:" + queue_type + " (queued work is not persisted)")
        issue_indexer = parser.get("indexer", "ISSUE_INDEXER_TYPE", fallback="bleve").strip().lower()
        if issue_indexer in {"elasticsearch", "meilisearch"}:
            external_dependencies.add("issue indexer:" + issue_indexer)
        if parser.getboolean("indexer", "REPO_INDEXER_ENABLED", fallback=False):
            repo_indexer = parser.get("indexer", "REPO_INDEXER_TYPE", fallback="bleve").strip().lower()
            if repo_indexer == "elasticsearch":
                external_dependencies.add("repository indexer:elasticsearch")
        default_type = parser.get("storage", "STORAGE_TYPE", fallback="local").strip().lower() or "local"
        for component, section in STORAGE_SECTIONS.items():
            storage_type = parser.get(section, "STORAGE_TYPE", fallback=default_type).strip().lower() or default_type
            if storage_types[component] == "unknown":
                storage_types[component] = storage_type
            elif storage_types[component] != storage_type:
                storage_types[component] = "mixed"

    core_components = {
        "database": database,
        "app_ini": app_ini_found,
        "repository_data": repositories,
    }
    waived_core_components = ["repository_data"] if allow_empty_repositories and not repositories else []
    core_components_look_present = all(
        found or component in waived_core_components for component, found in core_components.items()
    )
    missing_required_components = [
        component for component in required_components if not optional_components[component]
    ]
    file_basenames = {PurePosixPath(name).name for name in file_names}
    ssh_host_key_pairs = [
        {"private_key": name, "public_key": name + ".pub"}
        for name in sorted(ssh_host_key_names)
    ]
    ssh_host_keys_missing = [
        name for pair in ssh_host_key_pairs for name in pair.values() if name not in file_basenames
    ]

    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "archive_count": len(paths),
        "entry_count": len(names),
        "unsafe_archive_paths_ignored": unsafe_archive_paths_ignored,
        "zip_crc_checks_in_input_order": integrity_checks,
        "core_components": core_components,
        "per_archive_core_components": per_archive_core_components,
        "core_components_look_present": core_components_look_present,
        "waived_core_components": waived_core_components,
        "database_candidates": database_candidates,
        "optional_component_candidates": optional_components,
        "configured_storage_type_by_component": storage_types,
        "components_using_external_minio_storage": [
            component for component, storage_type in storage_types.items() if storage_type == "minio"
        ],
        "configured_path_settings_to_review": sorted(configured_path_settings),
        "database_type_configured_in_app_ini": (
            next(iter(configured_database_types))
            if len(configured_database_types) == 1
            else "mixed" if configured_database_types else None
        ),
        "configured_recovery_dependencies_needing_attention": sorted(external_dependencies),
        "required_optional_components": list(required_components),
        "missing_required_optional_components": missing_required_components,
        "database_candidate_found": database,
        "repository_data_candidate_found": repositories,
        "common_storage_data_candidate_found": storage,
        "app_ini_found": app_ini_found,
        "app_ini_settings_inspected": bool(config_files),
        "secret_key_configured_in_app_ini": config["secret_key_configured"],
        "oauth_jwt_secret_configured_in_app_ini": config["oauth_jwt_secret_configured"],
        "built_in_ssh_server_enabled": ssh_enabled,
        "ssh_host_key_candidates": ssh_host_key_pairs,
        "ssh_host_key_candidates_look_present": not ssh_host_keys_missing if ssh_enabled else None,
        "missing_ssh_host_key_candidates": ssh_host_keys_missing,
        "limitations": [
            "Checks archive names and selected app.ini settings only; it does not validate database contents, every configured path, or file integrity.",
            "Custom repository/storage paths and secrets stored in external files need operator review.",
            "Absolute archive paths and paths containing parent-directory traversal are ignored as recovery candidates.",
            "SSH host-key checks match basenames only and may not reflect custom APP_DATA_PATH layouts.",
            "A passing inventory is not a restore test or proof of recoverability.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", help="tar, tar.gz, tgz, or zip backup archives")
    parser.add_argument("--report", help="write JSON report to a new file (default: stdout)")
    parser.add_argument("--verify-integrity", action="store_true", help="read each ZIP entry and verify its CRC; other formats are reported unsupported")
    parser.add_argument("--require-component", action="append", choices=OPTIONAL_COMPONENTS, default=[], metavar="NAME", help="require an optional component; repeat for each (" + ", ".join(OPTIONAL_COMPONENTS) + ")")
    parser.add_argument("--allow-empty-repositories", action="store_true", help="waive the repository candidate check for an instance known to contain no repositories")
    args = parser.parse_args()
    try:
        report = inspect(args.archives, args.verify_integrity, args.require_component, args.allow_empty_repositories)
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
    except (OSError, EOFError, RuntimeError, lzma.LZMAError, zlib.error, tarfile.TarError, zipfile.BadZipFile, ValueError, configparser.Error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
