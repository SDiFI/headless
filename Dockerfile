FROM python:3.11-slim

WORKDIR /app
RUN pip install gunicorn
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

EXPOSE 5000

ENTRYPOINT [ \
    "gunicorn", \
     "--bind=0.0.0.0:5000", \
     "--access-logfile=-", \
     "--error-logfile=-", \
    "--access-logformat", \
    "%(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"", \
    "main:app" \
]
