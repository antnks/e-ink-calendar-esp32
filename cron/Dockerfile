FROM alpine

RUN apk update
RUN apk add wget python3 bash netcat-openbsd py3-pip imagemagick firefox
RUN pip3 install icalendar recurring_ical_events --break-system-packages

COPY process_month.py /app/
COPY pull_calendar.sh /app/
COPY template.shtml   /app/

ARG BASE_DIR=/app
ARG ICAL_SECRET_URL="https://calendar.google.com/calendar/ical/xxx%40group.calendar.google.com/private-xxx/basic.ics"
ARG EID_IP="192.168.1.1"
ARG EID_PORT="80"
ENV BASE_DIR=$BASE_DIR
ENV ICAL_SECRET_URL=$ICAL_SECRET_URL
ENV EID_IP=$EID_IP
ENV EID_PORT=$EID_PORT

ENTRYPOINT /app/pull_calendar.sh

