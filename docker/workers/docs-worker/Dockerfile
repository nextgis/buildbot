# buildbot-worker for build sphinx documentations

FROM harbor.nextgis.net/ngqgis/ngqgis/ubuntu-worker:jammy

# This will make apt-get install without question
ARG DEBIAN_FRONTEND=noninteractive

# Add additional ubuntu packages
RUN apt-get update \
  && apt-get install -y \
    cmake git ssh rsync \
    texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
    texlive-lang-cyrillic texlive-fonts-extra latexmk \
    hunspell-en-gb hunspell-en-us myspell-ru python3-enchant \
  && pip3 install sphinx==5.3.0 sphinxcontrib-httpdomain sphinx-bootstrap-theme sphinxcontrib-spelling sphinx_rtd_theme docutils==0.16 \
  && apt-get clean && apt-get autoclean \
  && rm -rf /var/cache/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
  && git clone https://github.com/nextgis/kotlin_sphinx.git \
  && git clone https://github.com/nextgis/anarchy_sphinx.git \
  && pip3 install -e ./kotlin_sphinx \
  && pip3 install -e ./anarchy_sphinx

COPY ./docs-worker/ssh_config /root/.ssh/config

RUN echo "Ivan Barsukov <ivan.barsukov@nextgis.com>" > /worker/info/admin \
    && echo "Ubuntu 22.04 (Jammy Jellyfish) environment for Sphinx documentation" > /worker/info/host
