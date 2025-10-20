# buildbot-worker

FROM harbor.nextgis.net/ngqgis/ngqgis/ubuntu-worker:jammy

RUN mkdir /android-ndk \
    && curl https://dl.google.com/android/repository/android-ndk-r25c-linux.zip --output /tmp/ndk.zip \
    && unzip /tmp/ndk.zip -d /tmp/android-ndk \
    && mv /tmp/android-ndk/android-ndk-*/* /android-ndk \
    && rm -r /tmp/*
RUN echo "Ivan Barsukov <ivan.barsukov@nextgis.com>" > /worker/info/admin \
    && echo "Ubuntu 24.04 (Noble Numbat) environment with Android NDK r25c for cross-compilation" > /worker/info/host