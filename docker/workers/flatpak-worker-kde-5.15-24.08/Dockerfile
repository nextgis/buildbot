FROM alpine:3.22

# Locale/env similar to flatpak-builder-lint image
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    TMPDIR=/tmp

# Base tooling
RUN apk add --no-cache \
    bash \
    ca-certificates \
    curl \
    flatpak \
    flatpak-builder \
    git \
    jq \
    rsync \
    zip \
    python3 \
    py3-pip \
    py3-twisted \
    py3-autobahn \
    py3-msgpack \
    py3-zope-interface \
    dumb-init \
    && update-ca-certificates \
    && python -m pip install --no-cache-dir --break-system-packages --no-deps buildbot-worker \
    && rm -rf /var/cache/apk/* /root/.cache/pip

# Ensure temp dirs exist with expected permissions
RUN rm -rf /tmp /var/tmp && mkdir -p -m 1777 /tmp /var/tmp

# Create buildbot user and working directory
RUN addgroup -S buildbot \
    && adduser -S -G buildbot buildbot \
    && mkdir -p /home/buildbot /worker \
    && mkdir -p /home/buildbot/.cache /home/buildbot/.local/share/flatpak \
    && chown -R buildbot:buildbot /home/buildbot /worker

# Switch to non-privileged user
USER buildbot

# Preconfigure Flathub remote and pre-pull commonly used runtimes/SDKs for caching
RUN flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo \
    && flatpak remote-modify --user --collection-id=org.flathub.Stable flathub \
    && flatpak install --user --assumeyes --noninteractive flathub \
        org.flatpak.Builder \
        org.kde.Platform//5.15-24.08 \
        org.kde.Platform.Locale//5.15-24.08 \
        org.kde.Sdk//5.15-24.08 \
        com.riverbankcomputing.PyQt.BaseApp//5.15-24.08 \
        org.kde.KStyle.Adwaita//5.15-24.08 \
        org.freedesktop.Platform.GL.default//24.08 \
        org.freedesktop.Platform.GL.default//24.08extra

# Switch back to non-privileged user
USER buildbot

WORKDIR /worker

# Copy worker configuration file
COPY ./common/buildbot.tac /worker/buildbot.tac

# Create info directory and add admin/host files
RUN mkdir -p /worker/info \
    && echo "Ivan Barsukov <ivan.barsukov@nextgis.com>" > /worker/info/admin \
    && echo "Provides environment with Flatpak tooling, preconfigured Flathub remote, and cached runtimes/SDKs" > /worker/info/host

CMD ["/usr/bin/dumb-init", "twistd", "--pidfile=", "-ny", "buildbot.tac"]