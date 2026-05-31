# buildbot-worker for build sphinx documentations

FROM harbor.nextgis.net/ngqgis/ngqgis/ubuntu-worker:noble

# This will make apt-get install without question
ARG DEBIAN_FRONTEND=noninteractive

# Add additional ubuntu packages
RUN apt-get update \
  && apt-get install -y \
    cmake git ssh rsync \
    texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
    texlive-lang-cyrillic texlive-fonts-extra latexmk \
    hunspell-en-gb hunspell-en-us python3-enchant \
    nodejs npm \
  && apt-get clean && apt-get autoclean \
  && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 install --break-system-packages sphinx==9.1.0 sphinxcontrib-httpdomain \
      sphinxcontrib-spelling pydata-sphinx-theme==0.17.0 Babel==2.18.0

# RUN git clone https://github.com/nextgis/kotlin_sphinx.git \
#   && git clone https://github.com/nextgis/anarchy_sphinx.git \
#   && pip3 install -e ./kotlin_sphinx \
#   && pip3 install -e ./anarchy_sphinx

COPY ./docs-worker/ssh_config /root/.ssh/config

RUN echo "Ivan Barsukov <ivan.barsukov@nextgis.com>" > /worker/info/admin \
    && echo "Ubuntu environment for Sphinx documentation" > /worker/info/host
