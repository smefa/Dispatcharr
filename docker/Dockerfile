# Define base image build arguments (must be before any FROM)
ARG REPO_OWNER=dispatcharr
ARG REPO_NAME=dispatcharr
ARG BASE_TAG=base

# --- Build frontend ---

FROM node:24 AS frontend-builder

WORKDIR /app/frontend
COPY ./frontend /app/frontend
# remove any node_modules that may have been copied from the host (x86)
RUN rm -rf node_modules || true; \
    npm install --no-audit --progress=false;
RUN    npm run build && \
    rm -rf node_modules .cache

# --- Redeclare build arguments for the next stage ---
ARG REPO_OWNER
ARG REPO_NAME
ARG BASE_TAG

# --- Upstream Intel media driver (amd64 only) ---
# The floating base image can ship Ubuntu's stock iHD_drv_video.so (~17 MB), which
# breaks hevc_qsv ("Invalid FrameType:0") on Intel Arc. Upstream v0.33.0 builds the
# driver from source (~47 MB) and works. Pinned by digest on purpose: do NOT use a
# floating tag, that is how this regression happened.
FROM --platform=linux/amd64 ghcr.io/dispatcharr/dispatcharr:latest@sha256:96bc548978c68e684677da7895692eeeefb7f0b2edfa38311dac2b702c61d236 AS intel-driver

# --- Final image based on the dynamic base ---
FROM ghcr.io/${REPO_OWNER}/${REPO_NAME}:${BASE_TAG} AS final
ENV VIRTUAL_ENV=/dispatcharrpy
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /app

# Replace Ubuntu's iHD driver with the known-good upstream build (see intel-driver stage).
# Nothing after this point may reinstall intel-media-va-driver.
ARG TARGETARCH
RUN --mount=type=bind,from=intel-driver,source=/usr/local/lib/x86_64-linux-gnu/dri,target=/mnt/intel-dri \
    if [ "$TARGETARCH" = "amd64" ]; then \
    install -D -m 0755 /mnt/intel-dri/iHD_drv_video.so /usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so; \
    fi

# Copy application code
COPY . /app
# Copy nginx configuration
COPY ./docker/nginx.conf /etc/nginx/sites-enabled/default
# Fix line endings and make entrypoint scripts executable
RUN for f in /app/docker/entrypoint*.sh; do \
    if [ -f "$f" ]; then \
    sed -i 's/\r$//' "$f" && chmod +x "$f"; \
    fi; \
    done
# Clean out existing frontend folder
RUN rm -rf /app/frontend
# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Add timestamp argument
ARG TIMESTAMP

# Update version.py with build timestamp if provided
RUN if [ -n "$TIMESTAMP" ]; then \
    echo "Updating timestamp to ${TIMESTAMP} in version.py" && \
    sed -i "s|__timestamp__ = None.*|__timestamp__ = '${TIMESTAMP}'    # Set during CI/CD build process|" /app/version.py && \
    cat /app/version.py; \
    fi

ENTRYPOINT ["/app/docker/entrypoint.sh"]