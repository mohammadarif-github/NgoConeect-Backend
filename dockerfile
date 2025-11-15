FROM python:3.11-alpine3.19
LABEL maintainer="lexaeon.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts
COPY ./ngoconnect /app
WORKDIR /app 
EXPOSE 8000

RUN apk update && \
    apk upgrade && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    rm -rf /var/cache/apk/* && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    mkdir -p /var/log && \
    mkdir -p /app/logs && \
    touch /var/log/uwsgi.log && \
    chown -R django-user:django-user /vol && \
    chown -R django-user:django-user /var/log && \
    chown -R django-user:django-user /app/logs && \
    chmod -R 755 /vol && \
    chmod -R 755 /var/log && \
    chmod -R 755 /app/logs && \
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

ARG GITHUB_ACTIONS=false

USER django-user

CMD ["run.sh"]