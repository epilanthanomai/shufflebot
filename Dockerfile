FROM python:alpine as base

FROM base as build
RUN apk add --update build-base python3-dev
COPY requirements.txt /
RUN mkdir /build
RUN pip install --prefix=/build -r /requirements.txt

FROM base
ENV ROOT /bot
WORKDIR $ROOT
COPY --from=build /build /usr/local
COPY shufflebot.py discobot.py $ROOT/
COPY decks/ $ROOT/decks/
CMD python3 shufflebot.py

ARG SHUFFLEBOT_VERSION
