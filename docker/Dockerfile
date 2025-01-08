FROM python:3.13-slim-bookworm

WORKDIR /releasenote
COPY main.py /releasenote/main.py
COPY requirements.txt /releasenote/requirements.txt

RUN pip install -r requirements.txt
RUN chmod +x /releasenote/main.py

ENTRYPOINT ["/releasenote/main.py"]
