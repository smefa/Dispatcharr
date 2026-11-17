#!/usr/bin/env python3
"""Prepare and validate review-only upstream release repairs."""

import argparse
import json
from pathlib import Path
import re
import subprocess


TAG_PATTERN = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")
REPAIR_REF = "refs/heads/release-repair"
TRAILER = "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"


def git(source, *args, check=True):
    try:
        return subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-C", str(source), *args],
            check=check, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as error:
        error.add_note(error.stderr or error.stdout or "Git returned no diagnostic output.")
        raise


def protected_index(source):
    entries = git(source, "ls-files", "--stage", "-z", "--", ".github").stdout
    result = {}
    for entry in entries.split("\0"):
        if entry:
            attributes, path = entry.split("\t", 1)
            mode, sha, stage = attributes.split()
            if stage != "0":
                raise RuntimeError("Workflow/configuration conflicts require human review.")
            result[path] = [mode, sha]
    return result


def protected_commit(source, commit):
    entries = git(source, "ls-tree", "-r", "-z", commit, "--", ".github").stdout
    result = {}
    for entry in entries.split("\0"):
        if entry:
            attributes, path = entry.split("\t", 1)
            mode, _, sha = attributes.split()
            result[path] = [mode, sha]
    return result


def prepare(source, tag):
    if not TAG_PATTERN.fullmatch(tag):
        raise ValueError("Only stable vX.Y.Z release tags are supported.")
    if git(source, "status", "--porcelain").stdout:
        raise RuntimeError("Repair preparation requires a clean checkout.")
    marker = f"refs/tags/xc-profile-upstream/{tag}"
    if git(source, "ls-remote", "origin", marker).stdout:
        raise RuntimeError(f"{tag} has already been published; no repair is needed.")
    base = git(source, "rev-parse", "HEAD").stdout.strip()
    git(source, "fetch", "--no-tags", "upstream", f"refs/tags/{tag}")
    upstream = git(source, "rev-parse", "FETCH_HEAD^{commit}").stdout.strip()
    merged = git(source, "merge", "--no-ff", "--no-commit", upstream, check=False)
    if merged.returncode and not git(source, "ls-files", "--unmerged").stdout:
        raise RuntimeError(merged.stderr or merged.stdout)
    return {
        "tag": tag, "base": base, "upstream": upstream,
        "protected": protected_index(source),
    }


def package(source, state, destination):
    if git(source, "rev-parse", "HEAD").stdout.strip() != state["base"]:
        raise RuntimeError("The agent must not create commits or change HEAD.")
    git(source, "add", "--all")
    if protected_index(source) != state["protected"]:
        raise RuntimeError("The agent changed .github configuration; refusing publication.")
    git(source, "diff", "--cached", "--check")
    has_merge = git(source, "rev-parse", "--verify", "MERGE_HEAD", check=False).returncode == 0
    difference = git(source, "diff", "--cached", "--quiet", check=False)
    if difference.returncode not in (0, 1):
        raise RuntimeError(difference.stderr or difference.stdout)
    has_changes = difference.returncode == 1
    if not has_merge and not has_changes:
        raise RuntimeError("The agent produced no repair. Inspect the failed run manually.")
    git(source, "commit", "-m", f"Repair XC profile compatibility with {state['tag']}",
        "-m", TRAILER)
    git(source, "merge-base", "--is-ancestor", state["upstream"], "HEAD")
    git(source, "update-ref", REPAIR_REF, "HEAD")
    destination.mkdir(parents=True, exist_ok=True)
    git(source, "bundle", "create", str(destination / "repair.bundle"),
        REPAIR_REF, f"^{state['base']}")


def validate(source, tag, bundle):
    # Reconstruct the expected merge with trusted code, not artifact metadata.
    state = prepare(source, tag)
    git(source, "bundle", "verify", str(bundle))
    git(source, "fetch", str(bundle), f"{REPAIR_REF}:refs/remotes/repair/candidate")
    candidate = git(source, "rev-parse", "refs/remotes/repair/candidate").stdout.strip()
    git(source, "merge-base", "--is-ancestor", state["base"], candidate)
    git(source, "merge-base", "--is-ancestor", state["upstream"], candidate)
    if protected_commit(source, candidate) != state["protected"]:
        raise RuntimeError("The candidate changed .github beyond the upstream merge.")
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "package", "validate"])
    parser.add_argument("source", type=Path)
    parser.add_argument("tag")
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    if not TAG_PATTERN.fullmatch(args.tag):
        parser.error("Only stable vX.Y.Z release tags are supported.")
    if args.command == "prepare":
        args.artifact.write_text(json.dumps(prepare(args.source, args.tag)))
    elif args.command == "package":
        state = json.loads((args.artifact / "state.json").read_text())
        if state["tag"] != args.tag:
            raise RuntimeError("Release tag does not match the prepared merge.")
        package(args.source, state, args.artifact)
    else:
        print(validate(args.source, args.tag, args.artifact))


if __name__ == "__main__":
    main()
