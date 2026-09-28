"""
scripts/package_submission.py
Packages the submission folder into a compliant submission.zip for Kaggle.
Ensures agent.yaml is at the root of the archive and prints MD5 + size verification.
"""

from __future__ import annotations
import hashlib
import os
import sys
import zipfile

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.validate_submission import validate_submission_dir


def package_submission(source_dir: str, output_zip: str):
    print("=" * 60)
    print("PACKAGING GEMMA 4 DEVELOPER AGENT SUBMISSION")
    print(f"Source: {source_dir}")
    print(f"Output: {output_zip}")
    print("=" * 60)

    # Step 1: Pre-flight validation
    if not validate_submission_dir(source_dir):
        print("\n[ERROR] Packaging aborted due to validation errors.")
        sys.exit(1)

    # Step 2: Create zip archive
    if os.path.exists(output_zip):
        os.remove(output_zip)

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir).replace("\\", "/")
                zf.write(full_path, arcname=rel_path)
                print(f"  + Added: {rel_path}")

    # Step 3: Verify zip contents
    with zipfile.ZipFile(output_zip, "r") as zf:
        names = zf.namelist()
        if "agent.yaml" not in names:
            print("[ERROR] Verification failed: agent.yaml is not at the root of submission.zip!")
            sys.exit(1)

    # Step 4: Calculate MD5 and size
    size_bytes = os.path.getsize(output_zip)
    hasher = hashlib.md5()
    with open(output_zip, "rb") as f:
        hasher.update(f.read())
    md5_hash = hasher.hexdigest()

    print("-" * 60)
    print(f"[SUCCESS] Packaged {len(names)} files into {os.path.basename(output_zip)}")
    print(f"  Archive Size: {size_bytes / 1024:.2f} KB ({size_bytes} bytes)")
    print(f"  MD5 Checksum: {md5_hash}")
    print(f"  Root Entry Verified: agent.yaml")
    print("=" * 60)


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = os.path.join(base_dir, "submission")
    dest = os.path.join(base_dir, "submission.zip")
    package_submission(src, dest)
