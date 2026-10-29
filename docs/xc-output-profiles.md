# Dispatcharr with XC Output-Profile Links

**This fork adds profile-specific Xtream Codes server URLs and live-stream
output-profile badges.**

**XC server URL:** `http://YOUR_SERVER:9191/low`

**Docker image:** `ghcr.io/smefa/dispatcharr:xc-profile`

This is an independently maintained Dispatcharr fork, not an official upstream
image. It keeps **Xtream Codes (XC) output-profile URLs** and **live-stream
output-profile badges** available while following upstream stable releases.
Output profiles and transcoding themselves are upstream features; this fork
adds a convenient way to select a profile through an XC server URL.

### Use an output profile in your XC app

1. In **Settings > Output Profiles**, create or edit an unlocked output profile
   with the transcoding settings you need, and keep **Is Active** enabled.
2. Set **Xtream Codes URL ending** to a unique name such as `low` and save.
   Use letters, digits, hyphens or underscores, up to 64 characters. Avoid
   names that differ only by letter case. Leaving the field empty disables
   that profile's named URL ending.
3. In your IPTV app's Xtream Codes login, use
   `http://YOUR_SERVER:9191/low` as the **server URL**, with your usual
   Dispatcharr XC username and password. Replace the host, port and scheme
   with your actual address; use HTTPS when accessing it over the internet.

For example, `/low/player_api.php` is handled as
`/player_api.php?output_profile=low`, and `/low/live/USER/PASSWORD/123.ts`
selects the same profile for live playback. A numeric prefix such as `/3`
selects output profile ID `3`; use a nonnumeric name for a named URL ending.
The profile must exist and be active. Unprefixed URLs remain available.

This is a live-stream output-profile selector, not a promise of VOD or
catch-up transcoding. Your XC client must retain the server URL's path prefix
when requesting live streams. Live connection cards in **Stats** show badges
for the active output profiles so you can check which profile is in use.
The URL does not replace authentication or grant additional channel access.

### Install and keep the fork

Use **`ghcr.io/smefa/dispatcharr:xc-profile`** instead of the upstream image
in your Docker deployment, keeping your existing `/data` volume and settings.
The published feature image targets **linux/amd64**. Pull the image and recreate
your container to install an update; publishing does not restart containers.

The daily release workflow is designed to merge upstream stable releases into
the patched `docker` branch and publish only after its checks pass. It also
restores this README section from `docs/xc-output-profiles.md` on `main` before
building, so upstream README edits do not silently remove the fork's usage
instructions. Conflicts or failed checks stop publication; they do not replace
the current image. An optional repair agent proposes draft fixes for review,
not automatic merges. These workflows must be merged into `main` to activate;
the repair agent additionally needs its documented secret and repository setting.
