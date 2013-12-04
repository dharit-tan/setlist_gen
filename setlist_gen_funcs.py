# pygame shit
import pygame
import pygame.midi as pymidi
import pygame.key as pykey
import pygame.event as pyevent
import pygame.fastevent as pyfastevent
from pygame.locals import *

# other imports
import socket
import signal
import datetime

HOST = 'localhost'
PORT = 8080

MIX_MIN = 20
MIX_MAX = 106
X_FADE_DIF = 80

X_FADER = (176, 0)

# did as much as I could, how the fuck do u pass decks and sock for closing?
def handler(signum, frame):
	pymidi.quit()
	pygame.quit()

# class def
class Deck:
	def __init__(self, name):
		# constants
		self.PLAY = None
		self.EQ_HI = None
		self.EQ_MID = None
		self.EQ_LO = None
		self.FILT = None
		self.VOL = None
		self.DEFAULT_VOL = 127
		self.X_FADE_SIDE = 0
		self.name = name

		# instance variables
		self.aud = False
		self.x_fade = True
		self.vol = True
		self.eq_hi = 63
		self.eq_mid = 63
		self.eq_lo = 63
		self.eq = True
		self.filt = True
		self.play = False

	def update(self):
		self.eq = (self.eq_hi > MIX_MIN) or (self.eq_mid > MIX_MIN) or (self.eq_lo > MIX_MIN)
		self.aud = self.x_fade & self.vol & self.eq & self.filt & self.play

def debug(a, b):
	for i in [a, b]:
		print i.name, "aud?", i.aud
		for v in vars(i):
			if v == False:
				print v, "False"

def list_devices():
	for i in range(pymidi.get_count()):
		print pymidi.get_device_info(i)

# pass in timestamp - init_timestamp
def handle_timestamp(timestamp):
	s = "[" + str(timestamp)[:7] + "]"
	return s

def get_device():
	while True:
		try:
			device_id = input('Enter device number: ')
			device = pymidi.Input(device_id)
		except NameError:
			print 'NameError, try again... '
		except pymidi.MidiException:
			print 'MidiException, try again...'
		except SyntaxError:
			print 'SyntaxError, try again...'
		else:
			return device

def connect_to_traktor():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((HOST, PORT))
	sock.listen(1)
	(conn, addr) = sock.accept()
	conn.send("HTTP/1.0 200 OK\r\n\r\n")
	print "Connected to traktor"
	return conn, sock

def handle_midi(e, deck_A, deck_B, focused_deck):
	for deck in [deck_A, deck_B]:
		if (e.status, e.data1) == deck.PLAY:
			if e.data2 == 127:
				deck.play = True
			else:
				deck.play = False
		if (e.status, e.data1) == deck.VOL:
			if e.data2 > (deck.DEFAULT_VOL / 3):
				deck.vol = True
			else:
				deck.vol = False
		if (e.status, e.data1) == deck.EQ_HI:
			deck.eq_hi = e.data2
		if (e.status, e.data1) == deck.EQ_MID:
			deck.eq_mid = e.data2
		if (e.status, e.data1) == deck.EQ_LO:
			deck.eq_lo = e.data2
		if (e.status, e.data1) == deck.FILT:
			if (e.data2 > MIX_MIN) and (e.data2 < MIX_MAX):
				deck.filt = True
			else:
				deck.filt = False
		if (e.status, e.data1) == deck.VOL:
			if e.data2 > (deck.DEFAULT_VOL / 3):
				deck.vol = True
			else:
				deck.vol = False
		if (e.status, e.data1) == X_FADER:
			if abs(e.data2 - deck.X_FADE_SIDE) < X_FADE_DIF:
				deck.x_fade = True
			else:
				deck.x_fade = False


	# if focused_deck:
	# 	print "focused deck:", focused_deck.name
	# else:
	# 	print "no focused_deck"

	if focused_deck != deck_B and not deck_B.aud:
		deck_B.update()
		if deck_B.aud:
			return datetime.datetime.now()
	deck_B.update()

	if focused_deck != deck_A and not deck_A.aud:
		deck_A.update()
		if deck_A.aud:
			return datetime.datetime.now()
	deck_A.update()
	return None

def get_default_midi_val(prompt, decks):
	print prompt
	key_entered, midi_entered = False, False
	while not key_entered or not midi_entered:
		events = pyfastevent.get()
		for e in events:
			if e.type == pygame.KEYDOWN:
				if (e.key == pygame.K_RETURN) and (midi_entered == True):
					key_entered = True
			if e.type == pymidi.MIDIIN:
				val = e.data2
				midi_entered = True
		if decks.poll():
			midi_events = decks.read(1)
			events = pymidi.midis2events(midi_events, decks.device_id)
			for e in events:
				pyfastevent.post(e)
	return val