#!/bin/bash

log_error ()
{
	echo "$1"
	log_info "$1"
}

log_info ()
{
	logger "$0: $1"
}

# get script's dir
SCRIPT=`realpath $0`
DIR=`dirname $SCRIPT`

# if env does not override, use the script's dir
if [ -z "$BASE_DIR" ]
then
	log_info "BASE_DIR not defined, setting to $DIR"
	BASE_DIR=$DIR
fi

# file locations
ICAL_SAVE="$BASE_DIR/ical.txt"
HTML_TEMPLATE="$BASE_DIR/template.shtml"
HTML_RENDER="$BASE_DIR/render.html"
PNG_SAVE="$BASE_DIR/ical-raw.png"
PNG_CROP="$BASE_DIR/ical-crop.png"
PNG_BRW="$BASE_DIR/ical.png"
PBM_B_TEMP="$BASE_DIR/ical.b.pbm"
PBM_R_TEMP="$BASE_DIR/ical.r.pbm"
#ICAL_SECRET_URL="https://calendar.google.com/calendar/ical/xxx%40group.calendar.google.com/private-xxx/basic.ics"
#EID_IP="192.168.1.1"
#EID_PORT="80"

# headers
BCK_UP="EID0"
BCK_DN="EID1"
RED_UP="EID2"
RED_DN="EID3"
CLEAR="EID9"

log_info "download calendar to a temp file"
wget -q -O "$ICAL_SAVE" "$ICAL_SECRET_URL"
if [ ! -s "$ICAL_SAVE" ]
then
	log_error "Unable to download the calendar"
	exit 1
fi

log_info "parse and save only requsted month and the next one"
python3 "$BASE_DIR/process_month.py" "$ICAL_SAVE" "$HTML_TEMPLATE" "$HTML_RENDER" $1
if [ $? != 0 ]
then
	log_error "python code failed"
	exit 10
fi

log_info "detect firefox"
firefox --version > /dev/null
if [ $? != 0 ]
then
	log_error "Unable to run headless firefox"
	exit 2
fi

log_info "run firefox to make screenshot only"
firefox --headless --screenshot "$PNG_SAVE" "file://$HTML_RENDER" 1> /dev/null 2> /dev/null
log_info "crop area that fits our screen"
convert "$PNG_SAVE" -crop 1304x984+12+4 "$PNG_CROP"
if [ $? != 0 ]
then
	log_error "Unable to crop PNG"
	exit 3
fi

log_info "converting to black-red-white"
python3 "$BASE_DIR/convert-brw.py" "$PNG_CROP" "$PNG_BRW"

log_info "extract black channel to $PBM_B_TEMP"
convert "$PNG_BRW" -negate "$PBM_B_TEMP"

log_info "extract red channel to $PBM_R_TEMP"
convert "$PNG_BRW" -fill white +opaque red "$PBM_R_TEMP.png"
convert "$PBM_R_TEMP.png" -negate "$PBM_R_TEMP"

log_info "clear display"
cat <(echo -n $CLEAR) | nc -w 1 $EID_IP $EID_PORT
sleep 30

chunk=$((1304*984/8/2))
log_info "sending black top"
cat <(echo -n $BCK_UP) <(tail -n +3 "$PBM_B_TEMP" | dd bs=1 count=$chunk skip=0 2>/dev/null)      | nc -w 10 $EID_IP $EID_PORT
log_info "sending black bottom"
cat <(echo -n $BCK_DN) <(tail -n +3 "$PBM_B_TEMP" | dd bs=1 count=$chunk skip=$chunk 2>/dev/null) | nc -w 10 $EID_IP $EID_PORT
log_info "sending red up"
cat <(echo -n $RED_UP) <(tail -n +3 "$PBM_R_TEMP" | dd bs=1 count=$chunk skip=0 2>/dev/null)      | nc -w 10 $EID_IP $EID_PORT
log_info "sending red down"
cat <(echo -n $RED_DN) <(tail -n +3 "$PBM_R_TEMP" | dd bs=1 count=$chunk skip=$chunk 2>/dev/null) | nc -w 10 $EID_IP $EID_PORT

log_info "done"

