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


def archive_members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_MEMBERS:
                raise ValueError(f"too many archive entries (limit {MAX_MEMBERS})")
            result = []
            for item in infos:
                config = None
                if PurePosixPath(item.filename).name.lower() == "app.ini" and item.file_size <= MAX_CONFIG_BYTES:
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
            if not item.isfile():
                continue
            config = None
            if PurePosixPath(item.name).name.lower() == "app.ini" and item.size <= MAX_CONFIG_BYTES:
                stream = archive.extractfile(item)
                if stream:
                    with stream:
                        config = stream.read(MAX_CONFIG_BYTES + 1)
            result.append((item.name, item.size, config))
        return result


def inspect(paths):
    names = []
    config_files = []
    app_ini_found = False
    for path in paths:
        members = archive_members(path)
        if len(names) + len(members) > MAX_MEMBERS:
            raise ValueError(f"too many archive entries across inputs (limit {MAX_MEMBERS})")
        for name, _size, config_bytes in members:
            normalized = str(PurePosixPath(name)).lower()
            names.append(normalized)
            app_ini_found |= PurePosixPath(normalized).name == "app.ini"
            if config_bytes is not None:
                if len(config_bytes) <= MAX_CONFIG_BYTES:
                    config_files.append(config_bytes)

    basenames = [PurePosixPath(name).name for name in names]
    database = any(
        name in {"forgejo.db", "gitea.db"} or name.endswith((".sql", ".sql.gz", ".dump"))
        for name in basenames
    )
    repositories = any("forgejo-repositories" in PurePosixPath(name).parts for name in names)
    storage = any(
        part in {"storage", "attachments", "lfs", "avatars", "repo-avatars", "packages"}
        for name in names for part in PurePosixPath(name).parts
    )
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

    return {
        "archive_count": len(paths),
        "entry_count": len(names),
        "database_candidate_found": database,
        "default_repository_directory_found": repositories,
        "common_storage_directory_found": storage,
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
    args = parser.parse_args()
    try:
        report = inspect(args.archives)
        payload = json.dumps(report, indent=2) + "\n"
        if args.report:
            with open(args.report, "x", encoding="utf-8") as output:
                output.write(payload)
        else:
            sys.stdout.write(payload)
    except (OSError, tarfile.TarError, zipfile.BadZipFile, ValueError, configparser.Error) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
