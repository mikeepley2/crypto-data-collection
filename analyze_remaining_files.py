#!/usr/bin/env python3
"""
Analyze remaining files to determine what's actually needed for production
vs development artifacts that can be cleaned up.
"""

import os
import glob


def categorize_remaining_files():
    """Categorize files to determine what can be removed."""

    categories = {
        "core_production": [],  # Essential for production
        "development_helpers": [],  # Development/deployment helpers
        "migration_scripts": [],  # One-time migration scripts
        "experimental": [],  # Experimental/testing
        "documentation": [],  # Documentation files
        "kubernetes": [],  # K8s manifests
        "questionable": [],  # Unclear necessity
    }

    # Get all Python files in root
    python_files = glob.glob("*.py")
    yaml_files = glob.glob("*.yaml") + glob.glob("*.yml")
    json_files = glob.glob("*.json")
    md_files = glob.glob("*.md")
    sh_files = glob.glob("*.sh")
    other_files = glob.glob("*")
    other_files = [
        f
        for f in other_files
        if not f.endswith((".py", ".yaml", ".yml", ".json", ".md", ".sh"))
    ]

    # Core production files (definitely keep)
    production_keywords = ["monitor_ml_features", "README", "LICENSE", ".gitignore"]

    # Development helpers (might keep)
    helper_keywords = ["deploy_", "update_", "populate_", "connection_pool", "enhance_"]

    # Migration/one-time scripts (probably remove)
    migration_keywords = ["migrate_", "backfill_", "add_", "restore_", "convert_"]

    # Experimental (probably remove)
    experimental_keywords = ["test-", "experiment", "temp", "trial", "poc"]

    print("=== REMAINING FILES ANALYSIS ===\n")

    # Analyze Python files
    print(f"PYTHON FILES ({len(python_files)}):")
    for file in sorted(python_files):
        if any(kw in file for kw in production_keywords):
            categories["core_production"].append(file)
            print(f"  [KEEP] {file} - Production essential")
        elif any(kw in file for kw in helper_keywords):
            categories["development_helpers"].append(file)
            print(f"  [MAYBE] {file} - Development helper")
        elif any(kw in file for kw in migration_keywords):
            categories["migration_scripts"].append(file)
            print(f"  [REMOVE?] {file} - Migration script")
        else:
            categories["questionable"].append(file)
            print(f"  [UNCLEAR] {file} - Needs review")

    print(f"\nYAML/JSON CONFIG FILES ({len(yaml_files + json_files)}):")
    for file in sorted(yaml_files + json_files):
        if "test-" in file or "manual-" in file or "trigger-" in file:
            categories["experimental"].append(file)
            print(f"  [REMOVE?] {file} - Test/manual file")
        elif file.startswith("enhanced-") or file.startswith("materialized-"):
            categories["kubernetes"].append(file)
            print(f"  [MAYBE] {file} - K8s manifest")
        else:
            categories["questionable"].append(file)
            print(f"  [UNCLEAR] {file} - Needs review")

    print(f"\nDOCUMENTATION ({len(md_files)}):")
    for file in sorted(md_files):
        categories["documentation"].append(file)
        print(f"  [KEEP] {file} - Documentation")

    print(f"\nOTHER FILES ({len(other_files + sh_files)}):")
    for file in sorted(other_files + sh_files):
        print(f"  [UNCLEAR] {file} - Needs review")
        categories["questionable"].append(file)

    # Summary
    print(f"\n=== SUMMARY ===")
    total = sum(len(files) for files in categories.values())
    print(f"Total files analyzed: {total}")
    for category, files in categories.items():
        if files:
            print(f"{category.upper()}: {len(files)} files")

    # Recommendations
    removable = len(categories["migration_scripts"]) + len(categories["experimental"])
    questionable = len(categories["questionable"])

    print(f"\n=== RECOMMENDATIONS ===")
    print(f"Definitely removable: {removable} files")
    print(f"Need review: {questionable} files")
    print(f"Potential space savings: ~{removable + questionable//2} files")

    return categories


if __name__ == "__main__":
    categorize_remaining_files()
