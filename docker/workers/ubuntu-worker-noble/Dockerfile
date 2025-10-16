# buildbot-worker

FROM ubuntu:noble

# This will make apt-get install without question
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && apt-get update \
  && apt-get install -y \
    apt-transport-https ca-certificates tzdata \
    python3-pip \
    curl \
    dumb-init \
    buildbot-worker \
    git devscripts debhelper equivs build-essential bash cmake \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && apt-get clean && apt-get autoclean \
  && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
  && dpkg-reconfigure -f noninteractive tzdata

# Copy worker configuration file
RUN mkdir -p /worker
COPY ./common/buildbot.tac /worker/buildbot.tac

# Create info directory and add admin/host files
RUN mkdir -p /worker/info \
    && echo "Ivan Barsukov <ivan.barsukov@nextgis.com>" > /worker/info/admin \
    && echo "Ubuntu 24.04 (Noble Numbat) environment" > /worker/info/host

WORKDIR /worker

CMD ["/usr/bin/dumb-init", "twistd3", "--pidfile=", "-ny", "buildbot.tac"]
