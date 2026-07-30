#!/usr/bin/env python3
"""Simple Dremio connection tester using a PAT stored in an environment variable.

This script does NOT store tokens. It reads the token from an env var and makes
one request to a configurable REST endpoint to verify connectivity.
"""
import os
import sys
import argparse
import requests


def parse_args():
    p = argparse.ArgumentParser(description="Test Dremio REST API connection using PAT from env var")
    p.add_argument("--host", required=True, help="Dremio host (host[:port]) e.g. dremio.example.com:9047")
    p.add_argument("--endpoint", default="/api/v3/catalog", help="REST endpoint path to call (default: /api/v3/catalog)")
    p.add_argument("--token-env", default="DREMIO_TOKEN", help="Environment variable that contains the PAT (default: DREMIO_TOKEN)")
    p.add_argument("--no-verify", action="store_true", help="Disable TLS verification (not recommended)")
    p.add_argument("--scheme", choices=["http", "https"], default="https", help="URL scheme (default: https)")
    return p.parse_args()


def main():
    args = parse_args()
    token = os.environ.get(args.token_env)
    if not token:
        print(f"Error: environment variable {args.token_env} is not set.", file=sys.stderr)
        print("Set it securely (see README) and retry.")
        sys.exit(2)

    url = f"{args.scheme}://{args.host}{args.endpoint}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers, verify=not args.no_verify, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(3)

    print(f"URL: {url}")
    print(f"Status: {resp.status_code}")
    # Print limited response body for quick inspection
    body = resp.text or ""
    print(body[:4000])

    if resp.status_code >= 400:
        sys.exit(4)


if __name__ == "__main__":
    main()
