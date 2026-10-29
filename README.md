<!-- xc-profile-fork:start -->
## What this fork adds: XC output-profile links

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
<!-- xc-profile-fork:end -->

# 🎬 Dispatcharr — Your Ultimate IPTV & Stream Management Companion

<p align="center">
  <img src="https://github.com/Dispatcharr/Dispatcharr/blob/main/frontend/src/images/logo.png?raw=true" height="200" alt="Dispatcharr Logo" />
</p>

---

## 📖 What is Dispatcharr?

Dispatcharr (pronounced like "dispatcher") is an **open-source powerhouse** for managing IPTV streams, EPG data, and VOD content with elegance and control.\
Born from necessity and built with passion, it started as a personal project by **[OkinawaBoss](https://github.com/OkinawaBoss)** and evolved with contributions from legends like **[dekzter](https://github.com/dekzter)**, **[SergeantPanda](https://github.com/SergeantPanda)** and **[Seth](https://github.com/sethwv)**.

> Think of Dispatcharr as the \*arr family's IPTV cousin — simple, smart, and designed for streamers who want reliability and flexibility.

---

## 🎯 What Can I Do With Dispatcharr?

Dispatcharr empowers you with complete IPTV control. Here are some real-world scenarios:

💡 **Consolidate Multiple IPTV Sources**\
Combine streams from multiple providers into a single interface. Manage, filter, and organize thousands of channels with ease.

📺 **Integrate with Media Centers**\
Use HDHomeRun emulation to add virtual tuners to **Plex**, **Emby**, or **Jellyfin**. They'll discover Dispatcharr as a live TV source and can record programs directly to their own DVR libraries.

📼 **Record with Built-in DVR**\
Schedule one-time or recurring recordings from the TV Guide, manage series rules, and optionally strip commercials with Comskip. Watch recordings while they're still in progress.

📡 **Create a Personal TV Ecosystem**\
Merge live TV channels with custom EPG guides from XMLTV or Schedules Direct. Generate schedules or use auto-matching to align channels with program data. Export as M3U, Xtream Codes API, or HDHomeRun device.

⏪ **Watch Catch-up / Timeshift**\
Replay recent programs from Xtream Codes providers that advertise archives. Catch-up sessions show up on the Stats page alongside live and VOD, with per-user and global controls.

🔧 **Transcode & Optimize Streams**\
Configure output profiles with FFmpeg transcoding to optimize streams for different clients (reduce bandwidth, standardize formats, or add audio normalization).

🔐 **Centralize VPN Access**\
Run Dispatcharr through a VPN container (like Gluetun) so all streams route through a single VPN connection. Your clients access geo-blocked content without needing individual VPNs, reducing bandwidth overhead and simplifying network management.

🚀 **Monitor & Manage in Real-Time**\
Track live, VOD, and catch-up sessions, client connections, and bandwidth usage with live statistics. Monitor buffering events and stream quality. Automatic failover keeps viewers connected when streams fail—seamlessly switching to backup sources without interruption.

👥 **Share Access Safely**\
Create multiple user accounts with granular permissions. Share streams via M3U playlists or Xtream Codes API while controlling which users access which channels, profiles, or features. Network-based access restrictions available for additional security.

🔌 **Extend with Plugins**\
Build custom integrations using Dispatcharr's robust plugin system. Automate tasks, connect to external services, or add entirely new workflows.

---

## ✨ Why You'll Love Dispatcharr

✅ **Stream Proxy & Relay** — Intercept and proxy IPTV streams with real-time client management\
✅ **M3U & Xtream Codes** — Import, filter, and organize playlists with multiple backend support\
✅ **EPG Matching & Generation** — XMLTV, Schedules Direct, or dummy guides; auto-match EPG to channels or generate custom schedules\
✅ **Built-in DVR** — Schedule recordings and series rules from the guide, with optional Comskip and in-progress playback\
✅ **XC Catch-up / Timeshift** — Proxy provider archives to clients, advertise catch-up in guides, and monitor sessions in Stats\
✅ **Video on Demand** — Stream movies and TV series with rich metadata and IMDB/TMDB integration\
✅ **Multi-Format Output** — Export as M3U, XMLTV EPG, Xtream Codes API, or HDHomeRun device\
✅ **Real-Time Monitoring** — Live, VOD, and catch-up connection stats, bandwidth tracking, and automatic failover\
✅ **Stream Profiles** — Configure how Dispatcharr connects to backend streams (VLC, FFmpeg, Streamlink, or custom commands)\
✅ **Output Profiles** — Transcode what stream profiles deliver before it reaches the client (e.g. AC3 for media servers, AAC for browsers) with fMP4 or MPEG-TS container selection\
✅ **Multi-User & Access Control** — Granular permissions and network-based access restrictions\
✅ **Plugin System** — Extend functionality with custom plugins for automation and integrations\
✅ **Fully Self-Hosted** — Total control, no third-party dependencies

---

# Screenshots

<div align="center">
  <img src="docs/images/channels.png" alt="Channels" width="750"/>
  <img src="docs/images/guide.png" alt="TV Guide" width="750"/>
  <img src="docs/images/stats.png" alt="Stats & Monitoring" width="750"/>
  <img src="docs/images/m3u-epg-manager.png" alt="M3U & EPG Manager" width="750"/>
  <img src="docs/images/vod-library.png" alt="VOD Library" width="750"/>
  <img src="docs/images/settings.png" alt="Settings" width="750"/>
</div>

---

## 🛠️ Troubleshooting & Help

- **General help?** Visit [Dispatcharr Docs](https://dispatcharr.github.io/Dispatcharr-Docs/)
- **Community support?** Join our [Discord](https://discord.gg/Sp45V5BcxU)

---

## 🚀 Get Started in Minutes

### 🐳 Quick Start with Docker (Recommended)

#### This fork's automatically updated XC profile image

Use `ghcr.io/smefa/dispatcharr:xc-profile` for this fork's XC output profile
URLs and live-stream output profile indicators. The `docker` branch contains
the patched application; `main` hosts the release monitor.

The **Rebuild XC Profile on Upstream Release** GitHub Actions workflow checks
the latest stable release of `Dispatcharr/Dispatcharr` once daily
(06:23 UTC; GitHub may delay scheduled runs). It can
also be started manually from the Actions tab. Prereleases are not selected.
For a new release, it merges the upstream tag into `docker`, runs the frontend
tests, builds the AMD64 image and runs the output profile backend tests before
publishing `:xc-profile` and a versioned tag such as `:xc-profile-v0.34.0`.
This preserves the existing image's AMD64 architecture.

Merge conflicts or failed tests/builds leave the current image untouched.
Inspect a failed run's logs and resolve conflicts on `docker` if necessary;
the next check retries releases without a successful publication marker.
Only after publication does the workflow create
`xc-profile-upstream/<upstream-tag>` in Git. The initial `v0.33.0` marker
records the existing successfully built feature image; it does not rebuild it.
Do not delete these markers unless you intend to rebuild a release.
Publication does not automatically restart your running container: pull the
new image and recreate the container to deploy it.

The fork's backend CI uses the upstream `dispatcharr/dispatcharr` base image,
as does the feature Dockerfile; no fork-specific `:base` image is required.
Upstream's PR compliance bot runs only in `Dispatcharr/Dispatcharr`, where its
GitHub App secrets and contribution policies apply. Release monitor integration
tests in `scripts/tests` run separately without an application image or bot
secrets; they require Git, which is not installed in the application base image.
The CI bootstrap explicitly initializes PostgreSQL with UTF-8 encoding, even
when the container's login shell defaults to the `C` locale.

#### Optional Copilot release repair agent

**Agent Repair for Upstream Release** attempts an application repair when a
scheduled or manually started release rebuild on `main` fails. It uses Copilot
CLI, not just a static merge script. It reads the failed run's logs, resolves
application conflicts, and proposes compatibility fixes while preserving the XC
profile features. Success is not guaranteed.

To enable it, merge the monitor/repair workflows into `main`, enable
**Allow GitHub Actions to create and approve pull requests** in the repository's
Actions settings, and add an Actions secret named `COPILOT_REPAIR_TOKEN`. Use a
fine-grained personal access token belonging to a Copilot subscriber with
**Copilot Requests** permission only; do not grant repository write permissions.
The normal Actions token handles attempt markers and PR creation in separate
jobs. Copilot usage is billed to the subscriber; the agent has a 20-minute timeout and at most
two autopilot continuations, not a guaranteed monetary spending cap. Never put
the token in code, logs, or issue comments.

There is **one automatic attempt per release**, recorded in the Git tag
`xc-profile-repair-attempt/<upstream-tag>` even if the attempt fails, to avoid
repeated daily AI charges. This is not a successful-publication marker. Do not
delete attempt tags unless you intend to permit another automatic AI attempt.
To explicitly retry, run the repair workflow manually with the failed rebuild's
run ID. Missing release
context, credentials, or configuration fails visibly without launching an agent.

The agent has file-reading/editing tools only, no shell or GitHub MCP tools,
and no repository write token. Trusted code packages its edits; a separate job
checks Git ancestry and rejects agent changes to `.github` before opening a
**draft PR against `docker`**. Workflow/configuration conflicts require human
intervention. The agent does not run application tests, merge the PR, publish
an image, or mark a release successful. Review the proposed changes and run
frontend/backend tests and a candidate image build before merging; PRs created
with the Actions token do not automatically trigger ordinary PR workflows.
After a reviewed repair is merged into `docker`, the next daily rebuild (or
a manual rebuild) runs the existing publication checks and publishes only if
they pass. Infrastructure failures may produce no useful repair; inspect the
repair workflow's logs rather than assuming a draft PR means success.

#### Upstream image

```bash
docker pull ghcr.io/dispatcharr/dispatcharr:latest
docker run -d \
  -p 9191:9191 \
  --name dispatcharr \
  -v dispatcharr_data:/data \
  ghcr.io/dispatcharr/dispatcharr:latest
```

> Customize ports and volumes to fit your setup.

First-time web setup is limited to local/private networks by default. If you are installing on a VPS or otherwise reaching the UI from a public IP, either create the admin with `docker exec <container> python manage.py createsuperuser`, or set `DISPATCHARR_SETUP_ALLOWED_IP` to your client IP (see comments in the compose files). The setup page also shows the IP Dispatcharr sees.

Behind a reverse proxy, set `DISPATCHARR_TRUSTED_PROXIES` to your proxy's IP or CIDR so Network Access, Stats, and rate limits see real client IPs (defaults trust private/loopback peers; use `none` to ignore forwarded headers).

The optional Reverse Proxy Auth setting (Settings → Reverse Proxy Auth) signs users in from an identity header asserted by an authenticating proxy such as Cloudflare Access, oauth2-proxy, or Authelia. It only honors proxies listed in an explicitly set `DISPATCHARR_TRUSTED_PROXIES`: the private/loopback default is not trusted for sign-in, so while that variable is unset the setting signs nobody in.

---

### 🐋 Docker Compose Options

| Use Case                    | File                                                    | Description                                                                                                   |
| --------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **All-in-One Deployment**   | [docker-compose.aio.yml](docker/docker-compose.aio.yml) | ⭐ Recommended! A simple, all-in-one solution — everything runs in a single container for quick setup.        |
| **Modular Deployment**      | [docker-compose.yml](docker/docker-compose.yml)         | Separate containers for Dispatcharr, Celery, Redis, and Postgres — perfect if you want more granular control. |
| **Development Environment** | [docker-compose.dev.yml](docker/docker-compose.dev.yml) | Developer-friendly setup with pre-configured ports and settings for contributing and testing.                 |

---

### 🛠️ Building from Source

> ⚠️ **Warning**: Not officially supported — but if you're here, you know what you're doing!

If you are running a Debian-based OS, use the `debian_install.sh` script. For other OS, contribute a script and we’ll add it!

---

## 🤝 Want to Contribute?

We welcome **PRs, issues, ideas, and suggestions**!

- Prior to contributing, please read the [CONTRIBUTING.md](https://github.com/Dispatcharr/Dispatcharr/blob/main/CONTRIBUTING.md)

> Whether it's writing docs, squashing bugs, or building new features, your contribution matters! 🙋

---

## 📚 Documentation & Roadmap

- 📖 **Documentation:** [Dispatcharr Docs](https://dispatcharr.github.io/Dispatcharr-Docs/)

**Upcoming Features (in no particular order):**

- 🎬 **VOD Management Enhancements** — Granular metadata control and cleanup of unwanted VOD content
- 📁 **Media Library** — Import local files and serve them over XC API
- 👥 **Enhanced User Management** — Customizable XC API output per user account
- 🔌 **Fallback Videos** — Automatic fallback content when channels are unavailable
- 📡 **HLS Output** — Serve streams as HLS alongside existing container formats

---

## ❤️ Shoutouts

A huge thank you to all the incredible open-source projects and libraries that power Dispatcharr. We stand on the shoulders of giants!

---

## ✉️ Connect With Us

Have a question? Want to suggest a feature? Just want to say hi?\
➡️ **[Open an issue](https://github.com/Dispatcharr/Dispatcharr/issues)** or reach out on [Discord](https://discord.gg/Sp45V5BcxU).

---

## 💖 Support Dispatcharr

[![Dispatcharr Open Collective](https://opencollective.com/dispatcharr/tiers/badge.svg)](https://opencollective.com/dispatcharr/contribute)

Open Collective provides a transparent way for anyone who finds value in Dispatcharr to support things like:
• Infrastructure costs (Domains, Servers, etc.)
• Apple Developer Program and Google Play Developer accounts
• Helping contributors dedicate more time to improving the project

Support is completely optional, and Dispatcharr will always remain free and open-source.

[Contribute here](https://opencollective.com/dispatcharr/contribute)

---

## ⚖️ License & Legal

Dispatcharr is licensed under **GNU AGPL v3.0**: For full license details, see [LICENSE](https://www.gnu.org/licenses/agpl-3.0.html).

Dispatcharr is a trademark of the Dispatcharr project. Use of the Dispatcharr name or logo requires permission from the maintainers.

---

### 🚀 _Happy Streaming! The Dispatcharr Team_
