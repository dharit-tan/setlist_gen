#!/usr/bin/env python
from setlist_gen_funcs import *

pygame.init()
pymidi.init()
pyfastevent.init()

signal.signal(signal.SIGINT, handler)

# initialize midi tuples and deck classes
deck_A = Deck("A")
deck_B = Deck("B")

deck_A.PLAY = (144, 12)
deck_A.EQ_HI = (176, 5)
deck_A.EQ_MID = (176, 7)
deck_A.EQ_LO = (176, 9)
deck_A.VOL = (176, 3)
deck_A.FILT = (176, 1)

deck_B.PLAY = (144, 13)
deck_B.EQ_HI = (176, 6)
deck_B.EQ_MID = (176, 8)
deck_B.EQ_LO = (176, 10)
deck_B.VOL = (176, 4)
deck_B.FILT = (176, 2)

list_devices()
decks = get_device()

try:
	pref = open("setlist_gen_preferences", "r")
	count = 0
	for line in pref:
		if count == 0:
			deck_A.DEFAULT_VOL = int(line)
		elif count == 1:
			deck_B.DEFAULT_VOL = int(line)
		elif count == 2:
			deck_A.X_FADE_SIDE = int(line)
		elif count == 3:
			deck_B.X_FADE_SIDE = int(line)
		count += 1
except IOError:
	pref = open("setlist_gen_preferences", "w")
	deck_A.DEFAULT_VOL = get_default_midi_val("Set deck A's volume to your default level and hit enter", decks)
	pref.write(str(deck_A.DEFAULT_VOL) + "\n")
	deck_B.DEFAULT_VOL = get_default_midi_val("Set deck B's volume to your default level and hit enter", decks)
	pref.write(str(deck_B.DEFAULT_VOL) + "\n")
	deck_A.X_FADE_SIDE = get_default_midi_val("Set the crossfader to deck A's side and hit enter", decks)
	pref.write(str(deck_A.X_FADE_SIDE) + "\n")
	deck_B.X_FADE_SIDE = get_default_midi_val("Set the crossfader to deck B's side and hit enter", decks)
	pref.write(str(deck_B.X_FADE_SIDE))

for var in [deck_A.X_FADE_SIDE, deck_B.X_FADE_SIDE]:
	if var > 63:
		var = 127
	else:
		var = 0

# print "a default vol:", deck_A.DEFAULT_VOL
# print "b default vol:", deck_B.DEFAULT_VOL
# print "a x fade side:", deck_A.X_FADE_SIDE
# print "b x fade side:", deck_B.X_FADE_SIDE

print "Set the crossfader to the deck that you will start with (or at least fucking move it)"
print "Don't forget to record!"
print "Begin broadcasting now"
conn, sock = connect_to_traktor()
print "Begin set"
print "-----------------------------------------------------------------------------------------------"

metadata_updated, timestamp_updated = False, False
log = open("log.txt", "w")

RECORD = (144, 18)

focused_deck = None
running = True
init_timestamp = None
timestamp = None
databool = False
asdf = False

# main loop			
while running:
	events = pyfastevent.get()
	for e in events:
		if e.type == pymidi.MIDIIN:
			if (e.status, e.data1) == RECORD:
				if e.data2 == 127:
					init_timestamp = datetime.datetime.now()
				if e.data2 == 0:
					running = False
			else:
				temp_timestamp = handle_midi(e, deck_A, deck_B, focused_deck)
				if temp_timestamp:
					timestamp = temp_timestamp
					timestamp_updated = True
				# else:
					# timestamp = old_timestamp
			# debug(deck_A, deck_B)
			# print timestamp


	if deck_A.aud and not deck_B.aud:
		focused_deck = deck_A
	if deck_B.aud and not deck_A.aud:
		focused_deck = deck_B
	# if not deck_A.aud and not deck_B.aud:
	# 	focused_deck = None

	if metadata_updated and timestamp_updated:
		t = handle_timestamp(timestamp - init_timestamp)
		print t, artist.strip("\n"), "-", title.strip("\n")
		log.write(t + " " + artist + " - " + title + "\n")
		metadata_updated, timestamp_updated, timestamp = False, False, None  # reset
		# old_timestamp = timestamp

	if decks.poll():
		midi_events = decks.read(10)
		events = pymidi.midis2events(midi_events, decks.device_id)
		for e in events:
			pyfastevent.post(e)

	data = conn.recv(4096)
	if not data:
		conn.close()
		print "Traktor closed the connection"
		running = False

	# if asdf:
	# 	data = "mofosmofosTITLE=fuckyoumanvorbis"
	# 	print data
	# if not asdf:
	# 	data = "asdfasdfARTIST="
	# 	print data
	# 	asdf = True

	# we've indicated that something went wrong and we need to use the prevline
	if databool:
		data = prevline + data  # use the previous line as well

	# if only ARTIST= is present and TITLE= is split up
	if "ARTIST=" in data and not "TITLE=" in data:
		databool = True  # save it for the next round

	# if only TITLE= is present and ARTIST= is split up
	if "TITLE=" in data and not "ARTIST=" in data:
		data = prevline + data

	# if they're both present
	if "ARTIST=" in data and "TITLE=" in data:
		if len(data.split("TITLE=")[1]) < 25:
			databool = True
		else:
			arr = data.split("ARTIST=")
			arr = arr[1].split("TITLE=")
			artist = arr[0]
			artist = artist[:-4]
			arr = arr[1].split("vorbis")
			title = arr[0]
			title = title[:-2]
			metadata_updated = True
			# print "metadata received"
			# print artist.strip("\n"), "-", title.strip("\n")
			databool = False

	prevline = data

	# end main loop

# the xx - angels (bodhi remix) + Clockwork & Avatism - Hail (Avatism Remix)

sock.close()
decks.close()
pymidi.quit()
pygame.quit()