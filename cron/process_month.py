import icalendar
import recurring_ical_events
from icalendar import Calendar
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import pytz
import locale
import sys

def append_event(idx, dt, ev):
	global month
	if idx not in month:
		month[idx] = list()
	month[idx].append([dt, ev])

def date_idx(d):
	return d.year*10000 + d.month*100 + d.day


if len(sys.argv) > 4:
	locale.setlocale(locale.LC_TIME, sys.argv[4])
mytz = pytz.timezone("Europe/Vilnius")

input_file = open(sys.argv[1], "r")
ical_events = Calendar().from_ical(input_file.read())

# today
today = datetime.today()
current_day   = today.day
current_month = today.month
current_year  = today.year

# find the first day of the current week
start_date = today - relativedelta(days=today.weekday())
start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
# add two weeks
end_date   = start_date + relativedelta(weeks=2) - relativedelta(days=1)
end_date   = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

start_date = mytz.localize(start_date)
end_date   = mytz.localize(end_date)

events = recurring_ical_events.of(ical_events).between(start_date, end_date)

month = dict()
for event in events:

	if event.name != "VEVENT":
		continue

	cal_date = event.get('dtstart').dt
	event_date = datetime.combine(cal_date, datetime.min.time())

	if event_date.tzinfo == None:
		event_date = mytz.localize(event_date)
	if event_date >= start_date and event_date <= end_date:
		dayindex = int(event_date.strftime('%Y%m%d'))
		summary = str(event.get('summary'))

		# check for full day event
		delta = event.get('dtend').dt - cal_date
		if delta.days >= 1:
			for i in range(0, delta.days):
				append_event(dayindex + i, None, summary)
		else:
			localtime = cal_date.astimezone(mytz).strftime("%H:%M")
			append_event(dayindex, localtime, summary)

##print(month)

# load template
template_file = open(sys.argv[2], "r")
template = template_file.read()
template = template.replace("${TODAY_DAY}",    today.strftime("%-d"))
template = template.replace("${TODAY_WEEKDAY}",today.strftime("%A"))
template = template.replace("${TODAY_MONTH}",  today.strftime("%B"))
template = template.replace("${TODAY_YEAR}",   today.strftime("%Y"))

# process current day
dic_idx = date_idx(today)
allday=""
timeday=""
color="black"

if today.weekday() >= 5:
	color="red"
if dic_idx in month:
	for event in month[dic_idx]:
		summary = event[1]
		##print(summary)
		# convention, if an event starts with an asterisk - it is public holiday
		if summary[0] == '*':
			color="red"
			summary=summary[2:]
		if event[0]:
			timeday += event[0] + " " + summary + "<br>"
		else:
			allday += summary + "<br>"
else:
	allday="☑"
template = template.replace("${TODAY_FULL_DAY_EVENTS}", allday)
template = template.replace("${TODAY_EVENTS}", timeday)
template = template.replace("${COLOR}", color)

row = '''\
<td style="width: 14%; vertical-align: top">
<span style="font-size: 50px; color: {color}; text-decoration-style: wavy; {decor};">
<strong>{curday}</strong><br></span><br>
<span style="font-size: 20px; color: {color};">
<strong>{allday}</strong>
{timeday}
</span>
</td>'''

# loop 14 days, leap day breaks date calculation
# https://github.com/antnks/e-ink-calendar-esp32/issues/5
day_counter=0
dayrow=""
loop_day = start_date
while day_counter < 14:
	color="black"
	decor="none"

	# TODO also detect public holiday
	if loop_day.weekday() >= 5:
		color="red"
	if loop_day.day == current_day:
		decor="display: inline-block; height: 70px; background: #bbbbbb"

	dic_idx = date_idx(loop_day)
	allday=""
	timeday=""
	if dic_idx in month:
		for event in month[dic_idx]:
			summary = event[1]
			##print(summary)

			# convention, if an event starts with an asterisk - it is public holiday
			if summary[0] == '*':
				color="red"
				summary=summary[2:]
			# if event[0] is None - it is a full day event
			if event[0]:
				timeday += event[0] + " " + summary + "<br>"
			else:
				allday += summary + "<br>"
	else:
		allday += "&nbsp;"

	if loop_day == start_date + relativedelta(weeks=1):
		dayrow+="\n</tr>\n<tr>"
	dayrow+=row.format(color=color, decor=decor, allday=allday, timeday=timeday, curday=loop_day.day)+"\n"

	loop_day += relativedelta(days=1)

template = template.replace("${DAY_ROW}", dayrow)

output_file = open(sys.argv[3], "w")
output_file.write(template)
output_file.close()

