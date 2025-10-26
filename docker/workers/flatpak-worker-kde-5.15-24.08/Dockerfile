FROM harbor.nextgis.net/ngqgis/ngqgis/ubuntu-worker:noble

# Locale/env similar to flatpak-builder-lint image
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    TMPDIR=/tmp

# Base tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    flatpak \
    flatpak-builder \
    git \
    jq \
    rsync \
    zip \
    python3 \
    python3-pip \
    python3-twisted \
    python3-autobahn \
    python3-msgpack \
    python3-zope.interface \
    dumb-init \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

# Ensure temp dirs exist with expected permissions
RUN rm -rf /tmp /var/tmp && mkdir -p -m 1777 /tmp /var/tmp

# Create info directory and add admin/host files
RUN mkdir -p /worker/info \
    && echo "Ivan Barsukov <ivan.barsukov@nextgis.com>" > /worker/info/admin \
    && echo "Provides Ubuntu 24.04 environment with preconfigured Flathub remote, and cached runtimes/SDKs" > /worker/info/host

# Update working directory
RUN mkdir -p /root/.ssh && mkdir -p /root/.cache /root/.local/share/flatpak \
    && touch /root/.ssh/authorized_keys \
    && chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

# Preconfigure Flathub remote and pre-pull commonly used runtimes/SDKs for caching
RUN flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo \
    && flatpak remote-modify --user --collection-id=org.flathub.Stable flathub
RUN flatpak install --user --assumeyes --noninteractive flathub \
        org.freedesktop.Platform.GL.default/x86_64/24.08 \
        org.freedesktop.Platform.GL.default/x86_64/24.08extra \
        org.kde.Platform/x86_64/5.15-24.08 \
        org.kde.Platform.Locale/x86_64/5.15-24.08 \
        org.kde.Sdk/x86_64/5.15-24.08
RUN flatpak install --user --assumeyes --noninteractive flathub \
    org.kde.KStyle.Adwaita/x86_64/5.15-24.08 \
    org.gtk.Gtk3theme.Breeze/x86_64/3.22 \
    com.riverbankcomputing.PyQt.BaseApp/x86_64/5.15-24.08
