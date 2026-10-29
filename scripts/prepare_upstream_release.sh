#!/usr/bin/env bash
set -euo pipefail

release_tag="${1:?An upstream release tag is required}"
if [[ ! "$release_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "::error::Unsupported stable release tag: $release_tag" >&2
  exit 1
fi

marker="refs/tags/xc-profile-upstream/$release_tag"
published="$(git ls-remote origin "$marker")"
if [[ -n "$published" ]]; then
  echo "changed=false" >> "$GITHUB_OUTPUT"
  echo "The patched image for $release_tag has already been published."
  exit 0
fi

git fetch --no-tags upstream "refs/tags/$release_tag"
upstream_sha="$(git rev-parse 'FETCH_HEAD^{commit}')"
if ! git merge --no-ff "$upstream_sha" \
  -m "Merge upstream $release_tag into patched Docker build" \
  -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"; then
  echo "::error::Upstream $release_tag could not be merged. Resolve the conflicts on docker; the published image has not been changed." >&2
  exit 1
fi

{
  echo "changed=true"
  echo "release_tag=$release_tag"
  echo "upstream_sha=$upstream_sha"
} >> "$GITHUB_OUTPUT"
