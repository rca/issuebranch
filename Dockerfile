FROM python:3.6
MAINTAINER Roberto Aguilar <roberto.c.aguilar@gmail.com>

COPY setup.py /usr/local/src/issuebranch/
COPY src/ /usr/local/src/issuebranch/src

WORKDIR /usr/local/src/issuebranch

RUN pip install .

WORKDIR /

CMD ["/bin/bash"]
