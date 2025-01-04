FROM python:3.13-slim-bookworm

WORKDIR /releasenote
COPY /src /releasenote/src
COPY requirements.txt /releasenote/requirements.txt

RUN adduser --disabled-password --gecos "" releasenote \
  && chown -R releasenote:releasenote /releasenote

USER releasenote

RUN pip install --user -r requirements.txt

ENTRYPOINT ["/releasenote/src/main.py"]