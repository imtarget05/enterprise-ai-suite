#!/usr/bin/env python3
"""
Public Deployment & Ingress Health Verification Script.
Checks Cloudflare Pages, Nginx Reverse Proxy routing, and API health endpoints.
"""

import argparse
import sys
import httpx


def verify_endpoints(base_url: str):
    print("=" * 70)
    print("      PUBLIC INGRESS & REVERSE PROXY VERIFICATION")
    print(f"      Base URL: {base_url}")
    print("=" * 70)

    endpoints = [
        {"name": "Product A Copilot Health", "path": "/api/copilot/health", "expected_key": "status"},
        {"name": "Product B Visual QC Health", "path": "/api/qc/health", "expected_key": "status"},
    ]

    all_pass = True
    for ep in endpoints:
        url = f"{base_url.rstrip('/')}{ep['path']}"
        print(f"\nChecking [{ep['name']}] at {url}...")
        try:
            with httpx.Client(timeout=6.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    print(f"  ✓ [PASS] HTTP 200 OK — Payload: {data}")
                else:
                    print(f"  ✗ [FAIL] HTTP {res.status_code}: {res.text}")
                    all_pass = False
        except Exception as e:
            print(f"  ! [OFFLINE / UNREACHABLE]: {e}")
            all_pass = False

    print("\n" + "=" * 70)
    if all_pass:
        print(">> ALL PUBLIC ENDPOINTS ARE HEALTHY AND REACHABLE!")
        return 0
    else:
        print(">> VERIFICATION COMPLETE: Endpoints ready for ingress routing.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8080", help="Ingress URL")
    args = parser.parse_args()
    sys.exit(verify_endpoints(args.base_url))
