import pygame as pg
import enchant
import numpy as np
import re
import copy
import os
import random as rand
import sys
import math
import time
from itertools import cycle
from datetime import datetime


# screen dimensions
WIDTH = 1200
HEIGHT = 750

# now some colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (7, 114, 105)
LIGHTBLUE = (79, 240, 240)
YELLOW = (254, 254, 34)
PURPLE = (153,153,255)
GREEN = (160,209,176)
ORANGE = (255, 165, 0)
GRAY  = (75,75,75)
LIGHTGRAY = (160,160,160)

# user defined events
FALL_EVENT = pg.USEREVENT + 0

# dice to choose letters via "rolling" them
four_dice = ["AAEEGN","ABBJOO","ACHOPS","AFFKPS","AOOTTW","CIMOTU","DEILRX","DELRVY","DISTTY","EEGHNW","EEINSU","EHRTVW","EIOSST","ELRTTY","HIMNUQu","HLNNRZ"]
five_dice = ["AAAFRS","AAEEEE","AAFIRS","ADENNN","AEEEEM","AEEGMU","AEGMNN","AFIRSY","BJKQXZ","CCENST","CEIILT","CEILPT","CEIPST","DDHNOT","DHHLOR","DHLNOR","DHLNOR","EIIITT","EMOTTT","ENSSSU","FIPRSY","GORRWV","IPRRRY","NOOTUW","OOOTTU"]


# general class for different types of buttons
class Pressable:
	def __init__(self,box_type,label,color,x,y,w,h, rounding=0):
	    self.type = box_type
	    self.clicked = False
	    self.rect = pg.Rect(x,y,w,h)
	    self.rounding = rounding
	    self.color = color
	    self.label = smallmono.render(label,True, WHITE)
	    self.enter = False
	    self.push_count = 0

	# cover responses to clicking, interacting based on element type
	def handle(self,event, outside=False):
	    if pg.mouse.get_pressed()[0]:
	        self.clicked = True
	    if (event.type == pg.MOUSEBUTTONUP):
	        self.clicked = False
	    if not pg.mouse.get_pressed()[0]:
	        self.clicked = False

	    if self.clicked:
	        if self.type == "text":    # save for now, maybe for name input!
	            self.color = BLUE
	            if event.type == pg.KEYDOWN:
	                if event.key == pg.K_RETURN:
	                    self.enter = True
	                    self.clicked = False
	                    self.cover()
	                if event.key == pg.K_BACKSPACE:
	                    self.text = self.text[:-1]
	                self.text += event.unicode
	                self.cover()
	        
	        if self.type == "button":
	            pg.mixer.Sound.play(button_sound)
	            # cover done box, new game, etc.
	            self.push_count = self.push_count + 1

	    # cram in a clearing option for the plot box
	    if not self.clicked:
	        if self.type == "text":
	            self.color = BLACK

	# more text stuff? maybe cursor blinking!
	def cover(self):
	    #cover up box, by overlaying smalller white box
	    pg.draw.rect(screen, WHITE, pg.Rect(self.rect.x+1 , self.rect.y, self.rect.w-1, self.rect.h-1))
	    if not self.enter:
	        text_surface = queenfont.render(self.text, True, BLACK)
	        screen.blit(text_surface, (self.rect.x+10, self.rect.y+10))
	    pg.display.update(self.rect)


# turn number of seconds into digital watch time format
def convert_time(time):
	#convert time from counter to mins:secs
	mins = str(int(time/60))
	if len(mins) == 1:
		mins = "0"+mins
	secs = 60*(time/60 - int(time/60))
	secs = str(int(secs))
	if len(secs) == 1:
		secs = "0"+secs
	converted = str(mins)+":"+str(secs)
	return converted


# consturct and return 2D array that is boggle board of characters
def gen_board(N):
	dice = list(five_dice)  # set up dice
	new_board = np.chararray((N,N))
	letter_surfs = np.empty((N,N),dtype=object)
	plus_surfs = np.empty((N,N),dtype=object)
	for i in range(0,N):
		for j in range(0,N):
			die = rand.choice(dice)
			dice.remove(die)
			letter = rand.choice(die) #0:26 to cut off capital letters, these could clash later with checking words
			letter_surfs[i][j] = queenfont.render(letter,True, PURPLE)
			# grab letter value first, if it is special
			value = get_val(letter)
			if value > 0:
				plus_surfs[i][j] = smallmel.render("+"+str(value),True, BLUE)
			if value == 0:
				plus_surfs[i][j] = smallqueen.render("",True, BLUE)
			new_board[i,j] = letter
	dice = list(five_dice) # put em all back
	return new_board, letter_surfs, plus_surfs


# return scrabble like mapping of letter to value
def get_val(letter):
	if letter in ["K","V"]:
		return 1
	if letter in ["Q","X"]:
		return 2
	if letter in ["J", "Z"]:
		return 3
	# if not a "special" letter, has no greater value
	return 0


# use scoring system to find total score f all your found words
def calc_score(wordbank):
	total = 0
	for word in wordbank:
		if "," in word:
			word = word.replace(",","")
		if len(word) == 4 or len(word) == 3:
			add = 1
		if len(word) == 5:
			add = 3
		if len(word) == 6:
			add = 5
		if len(word) == 7:
			add = 9
		if len(word) >= 8:
			add = 13
		letter_bonus = 0
		for letter in word:
			letter_bonus = letter_bonus + get_val(letter)
		
		total = total + add + letter_bonus
	return total


# open an external file that tracks every word ever found
# will eventually sort by alpha + length...
# that will do sortby first letter + shortest first
def update_totalbank(wordbank):
	lines = open("totalbank.txt").read().split("\n")
	# above lines are seperate words! (not planning on tracking frequency for now....)
	new_words = []
	length_dict = {}
	for word in wordbank:
		if word not in lines:
			# should have already covered for upper/lower case....
			new_words.append(word)
			if len(word) in length_dict:
				length_dict[len(word)].append(word)
			else:
				length_dict[len(word)] = [word]
	#now with all words, just do a simple length sort....
	for line in lines:
		if len(line) in length_dict:
			length_dict[len(line)].append(line)
		else:
			length_dict[len(line)] = [line]
	lines = lines + new_words
	open('totalbank.txt', 'w').close()  # clear file
	file = open('totalbank.txt', 'w')
	count = 0
	for key in sorted(length_dict, reverse=True):
		words = length_dict[key]
		for word in words:
			file.write(word)
			if count != len(lines) - 1:
				file.write("\n")
			count = count + 1
	file.close()


# write a single game score to a high scores text file (so its sorted!)
def write_score(name, score, num_words):
	name = name.upper()
	date_today = datetime.now().strftime("%m/%d/%Y")
	lines = open("scores.txt").read().split("\n")[2:]  #first two lines are header stuff
	if len(score) == 1:
		score = "0"+score
	# format new score
	add_line = "{name: <10}{score: ^10}{num_words: ^10}{date: >8}".format(name=name, num_words=num_words, score=score, date=date_today)
	lines.append(add_line)
	score_dict = {}
	for i in range(len(lines)):
		line_data = lines[i].split()
		if len(line_data) == 0:			# spurious new line, skip
			continue
		if line_data[1] not in score_dict:
			score_dict[line_data[1]] = [i]
		else:
			score_dict[line_data[1]].append(i)
	open('scores.txt', 'w').close()  # clear file
	file = open('scores.txt', 'w')
	file.write(score_header)	# write header
	file.write("\n")
	file.write("\n")
	# sort by highest score, and write according to index in read data
	for key in sorted(score_dict, reverse=True):
		indexes = score_dict[key]
		for index in indexes:
			file.write(lines[index])
			file.write("\n")
	file.close()


# store all your found words to a custom named txt file
def write_wordbank(wordbank):
	curr_score = str(calc_score(wordbank))
	filename = name+"_"+datetime.now().strftime("%m_%d_%Y")+"_score"+curr_score+"_wordbank"
	file = open(filename, "w")
	for word in wordbank:
		file.write(word+"\n")
	file.close()


# wrapping up score display once game over
def show_score(score, num_words, long_w):
	num_words_surf = bigcourier.render(num_words, True, PURPLE)
	score_surf = bigcourier.render(score, True, PURPLE)
	long_surf  = bigcourier.render(long_w, True, PURPLE)
	# show num_words, score, longest word
	b_1 = bigcourier.render("SCORE", True, LIGHTGRAY)
	b_2 = bigcourier.render("# WORDS", True, LIGHTGRAY)
	b_3 = bigcourier.render("LONGEST", True, LIGHTGRAY)
	screen.blit(over_img,[x_init-2,y_init-2])
	pg.display.update()
	# wait small time, longest, then mid, #, then longer, then score
	pg.time.wait(1200)
	text_w , text_h = bigcourier.size("LONGEST")
	screen.blit(b_3,[x_init+89,y_init+234])
	screen.blit(long_surf,[x_init+312,y_init+234])
	pg.display.update(pg.Rect(x_init+89, y_init+234, text_w, text_h))
	pg.time.wait(1200)
	text_w , text_h = bigcourier.size("# WORDS")
	screen.blit(b_2,[x_init+92,y_init+308])
	screen.blit(num_words_surf, [x_init+312, y_init+308])
	pg.display.update(pg.Rect(x_init+92, y_init+308, text_w, text_h))
	pg.time.wait(1200)
	text_w , text_h = bigcourier.size("SCORE")
	screen.blit(b_1,[x_init+92,y_init+384])
	screen.blit(score_surf, [x_init+312, y_init+384])
	pg.display.update(pg.Rect(x_init+92, y_init+384, text_w, text_h))
	#pg.time.wait(5000)  #10000


# render the wordbank, since a new word has been found. returns pygame surfaces of all the words
def bank_render(wordbank):
	word_surfs = []
	for word in wordbank:
		# dont add a comma if its the first word!
		if wordbank.index(word) != len(wordbank) - 1:
			word_surface = smallmono.render(word+",", True, GREEN)
		else:
			word_surface = smallmono.render(word, True, GREEN)
		word_surfs.append(word_surface)
	return word_surfs


# return the letter that matches the click position on the board
def get_letter(x,y,link):
	covered = False
	double_type = None
	x = int((x-x_init)/spacing) # sub xinit jump and divide by spacing to match board
	y = int((y-y_init)/spacing)
	for i in range(len(link)):
	#for piece in link:
		test_coord = link[i][0]
		if [x,y] == test_coord:
			covered = True
			# below sends info back about if you've retraced your steps in the word path
			if i == len(link) - 1:
				double_type = "last"
			elif i == len(link) - 2:
				double_type = "second"
			else:
				double_type = "pre"
	letter_match = board[x][y]
	if covered:
		letter_match = ""
	return letter_match, [x,y], double_type
	# to handle diags: if in circle on corners, dont take a new letter, 
	# once out of circles, check coords (by then, on desired diag!)


# check if word long enough, in US dict, and return the msg box response
def check_word(link):
	# use dictionary here
	# if word, add to word bank
	new_word = False
	letter_vals = []
	msg = ""
	word = ""
	coords = []
	for piece in link:
		if piece[0] not in coords:
			coords.append(piece[0])
		word = word + piece[1].decode("utf-8")
		letter_vals.append(get_val(piece[1].decode("utf-8")))
	if len(link) != len(coords):
		# if the link coords had any doubles!
		msg = "Double letters!"
		pg.mixer.Sound.play(wrong_sound)
	if len(link) == len(coords):
		if len(word) >= 3:
			words_to_check = [word]
			for i in range(len(word)):
				if word[i] == "Q":
					words_to_check.append(word[:i+1]+"U"+word[i+1:])  # grab extra q+u forms
			in_check = False
			for test_word in words_to_check:
				# check both dicts......
				if dictionary.check(test_word):
					in_check = True
				if dictionaryEXTRA.check(test_word):
					in_check = True
			if in_check:
				#this means its a word! includes Q or Qu check above...
				# but still need to modify word if so
				if (dictionary.check(word[0:1]+"U"+word[1:]) and word[0:1] == "Q"):
					word = word[0:1]+"U"+word[1:]
				elif (dictionaryEXTRA.check(word[0:1]+"U"+word[1:]) and word[0:1] == "Q"):
					word = word[0:1]+"U"+word[1:]

				if word in wordbank:
					pg.mixer.Sound.play(already_sound)
					msg = "Already in bank!"
					new_word = False
				else:
					wordbank.append(word)
					pg.mixer.Sound.play(correct_sound)
					msg = "New word, nice!"
					if sum(letter_vals) > 0:
						msg = "Nice, +"+str(sum(letter_vals))+" bonus!"
					new_word = True
			else:
				pg.mixer.Sound.play(wrong_sound)
				msg = "Not a real word!"
		else:
			pg.mixer.Sound.play(wrong_sound)
			msg = "Not long enough!"

	# create surf for msg that will be blitted
	msg_surf = melfont.render(msg, True, PURPLE)
	return new_word, msg_surf


# board has been clicked on, decide whether to build word
def handle_board(mouse_pos,clicked,link, msg_surf):
	new_word = False
	if clicked:   # so if in the link making stage
		letter,coords,double_type = get_letter(mouse_pos[0],mouse_pos[1], link)
		if letter != "":
			# not a repeat letter, dont skip!
			link.append([coords,letter])
		if letter == "" and double_type == "pre":
			# need to drop since doubled on letter that isn't last!
			msg_surf = melfont.render("Double letter!", True, PURPLE)
			pg.mixer.Sound.play(wrong_sound)
			link = []
			clicked = False
		if letter == "" and double_type == "second":
			# just pop off last letter so a "go back"?
			link.pop()

	if not clicked and len(link) > 1:         # word that isnt one letter
		new_word, msg_surf = check_word(link)
		link = []
	if not clicked and len(link) == 1:		  # weird case where clicked gets false dropped
		clicked = True
	return link, new_word, msg_surf, clicked


# wrap up concatenating two points that are the tiles to swich (with updates!)
def handle_tile_switch(mouse_pos, switch_tiles):
	# swtich_tiles is actually just matrix coords?
	x = mouse_pos[0]
	y = mouse_pos[1]
	x = int((x-x_init)/spacing) # sub xinit jump and divide by spacing to match board
	y = int((y-y_init)/spacing)
	if [x,y] not in switch_tiles:  # dont add same tile again!
		if len(switch_tiles) < 2:
			# take tile under mouse and add!
			switch_tiles.append([x,y])
		else:
			# drop first, use new!
			switch_tiles.pop(0)
			switch_tiles.append([x,y])
	return switch_tiles


pg.init()
# Set the width and height of the screen [width, height]
size = (WIDTH,HEIGHT)
screen = pg.display.set_mode(size)	 
pg.display.set_caption(":O") 
# Used to manage how fast the screen updates
clock = pg.time.Clock()

pg.font.init()

# fonts
rockfont = pg.font.Font("boggle_fonts/Rockwell.ttc", 24, bold=True)
courierfont = pg.font.Font("boggle_fonts/Courier.ttf", 24, bold=True)
smallcourier = pg.font.Font("boggle_fonts/Courier.ttf", 20, bold=True)
bigcourier = pg.font.Font("boggle_fonts/Courier.ttf", 38, bold=True)
monofont = pg.font.Font("boggle_fonts/DelugiaMonoPLBold.ttf", 30, bold=True)
smallmono = pg.font.Font("boggle_fonts/DelugiaMonoPLBold.ttf", 22, bold=True)
melfont  = pg.font.Font("boggle_fonts/A-OTF Folk Pro B.otf", 30, bold=True)
midmel   = pg.font.Font("boggle_fonts/A-OTF Folk Pro B.otf", 26, bold=True)
smallmel =pg.font.Font("boggle_fonts/A-OTF Folk Pro B.otf", 19, bold=True)
queenfont = pg.font.Font("boggle_fonts/QueenEmpress.ttf",32)
smallqueen = pg.font.Font("boggle_fonts/QueenEmpress.ttf",20)

# sounds
new_sound = pg.mixer.Sound("sounds/correct.wav")
wrong_sound = pg.mixer.Sound("sounds/wrong.wav")
correct_sound = pg.mixer.Sound("sounds/cool_wavy_short.wav")
already_sound = pg.mixer.Sound("sounds/minecraft_click.wav")
button_sound = pg.mixer.Sound("sounds/simple_click.wav")

# load images, pre-renders
board_img = pg.image.load("images/board.png").convert_alpha()
over_img = pg.image.load("images/game_over.png").convert_alpha()
pause_1 = pg.image.load("images/pause_screen_1.png").convert_alpha()
pause_2 = pg.image.load("images/pause_screen_2.png").convert_alpha()
pause_3 = pg.image.load("images/pause_screen_3.png").convert_alpha()
pause_imgs = cycle([pause_1, pause_2, pause_3])
score_prefix = melfont.render("Score: ", True, PURPLE)

# buttons
newgame_box = Pressable("button", "New Game", BLUE, 60, 631, 140, 50)
pause_box   = Pressable("button", "Pause", BLUE, 295, 631, 140, 50)
quit_box	= Pressable("button", "QUIT", GRAY, 185, 698, 120, 35)
save_box	= Pressable("button", "", None, 458, 573, 110, 56)
switch_box	= Pressable("button", "Swap Tiles", GRAY, 29, 532, 180, 46, rounding=5)
boxes = [newgame_box, pause_box, quit_box, save_box, switch_box]

# boggle board
spacing = 100
x_init = 30
y_init = 30
N = 5
board_rect = pg.Rect(x_init,y_init,500,500)
max_time = 100.5    # time per board, 80.5 is standard

# no words yet, "real" word table
dictionary = enchant.Dict("en_US")
# grab tWOL words too! 
dictionaryEXTRA= enchant.request_pwl_dict("TWL06.txt")

# get player name
name = sys.argv[1]

# initial state, score file
score_header = f"{'NAME' : <10}{'SCORE' : ^10}{'NUM_WORDS' : ^10}{'TIME' : >10}"
overall_time = 0
loop_c = 0        # track the number of loops
quit = False
newgame = False
endgame = False
clicked = False
pause = False
off_board = False
switching = False
msg_surf = courierfont.render(" ", True, GREEN)
link = []
wordbank = []
word_surfs = []
switch_tiles = []
screen.fill(WHITE)
screen.blit(board_img, (0,0))
pg.display.update()


# -------- Main Program Loop ----------- #
while not quit:
	# before we've done anything, "start timer"
	if loop_c == 0:
		t_0 = time.time()
	new_word = False
	# deal with game element interaction
	mouse_pos = pg.mouse.get_pos()
	box_colliding = False
	for event in pg.event.get():
	    if event.type == pg.QUIT:
	    	exit()
	    for box in boxes:
	        if box.rect.collidepoint(mouse_pos):
	            box.handle(event)
	            box_colliding = True
	    # handle position if in boggle board
	    if board_rect.collidepoint(mouse_pos) and newgame:
	    	off_board = False
	    	diag = False
	    	# need to cover going through exact diagonal corner
	    	# so check!
	    	for i in range(0,N):
	    		for j in range(0,N):
	    			if i != 0 and j != 0:
	    				x,y = mouse_pos
	    				dist = math.sqrt((x - (i*spacing+x_init))**2 + (y - (y_init + j*(spacing)))**2)
	    				if dist <= 20:
	    					diag = True

	    	if not diag:
	    		if not switching:
	    			# cover clicking, and making new link, or clicking and ending link
	    			if pg.mouse.get_pressed()[0] and not clicked:
	    				clicked = True
	    			elif pg.mouse.get_pressed()[0] and clicked:
	    				#pg.mixer.Sound.play(circle_sound)
	    				clicked = False
	    			link, new_word, msg_surf, clicked = handle_board(mouse_pos,clicked,link,msg_surf)
	    		# switch tile button has been pressed!
	    		if switching and pg.mouse.get_pressed()[0]:
	    			# track tiles clicked
	    			# first one switches for latest!
	    			handle_tile_switch(mouse_pos, switch_tiles)

	    if not board_rect.collidepoint(mouse_pos) and not box_colliding:
	    	if clicked:
	    		# so if not mousing over board, and not on any buttons
	    		# drop any link currently formed
	    		clicked = False
	    		msg_surf = melfont.render("Went off board!", True, PURPLE)
	    		link = []
	    	if not clicked:
	    		# also want to say, "dont draw the old link circle" = remove the circle
	    		off_board = True

	    if link == [] and newgame:
	    	break

	# if the newgame button has been pressed! deal with this first...
	if newgame_box.push_count > 0 and not pause:
		score = 0  					# zero the score here, in case ever want to re-blit before new game
		newgame = True
		wordbank = []
		link = []
		switch_tiles = []
		switch_box.push_count = 0
		if len(boxes) < 5:
			boxes.append(switch_box)
		overall_time = 0
		if endgame:
			endgame = False
			t_0 = time.time()
			#  possibly loop_c == 0?
		board, letter_surfs, plus_surfs = gen_board(N)
		msg_surf = courierfont.render(" ", True, GREEN)
		# have to re-render; wordbank is now empty
		word_surfs = bank_render(wordbank)

	# remove spurious pause presses
	if (pause_box.push_count > 0 and not newgame) or (pause_box.push_count > 0 and switching):
		pause_box.push_count = 0
	if (switch_box.push_count > 0 and not newgame) or (switch_box.push_count > 0 and pause):
		switch_box.push_count =  0

	# custom quit since event loop undermined
	if quit_box.push_count > 0:
		sys.exit()

	# now that we're paused, handle
	if newgame and pause:
		if pause_box.push_count > 0:
			# now here reset
			pause = False
			pause_box.push_count = 0
			t_0 = time.time()        # account for for no time passing!
		else:
			# still paused; blit pause screen
			cycle_now = time.time()
			if cycle_now - cycle_start >= 1:
				pause_curr = next(pause_imgs)
				cycle_start = time.time()
			screen.blit(pause_curr,[x_init-2,y_init-2])

	# save the wordbank, whether paused or not
	if save_box.push_count > 0:
		if len(wordbank) > 0:
			write_wordbank(wordbank)
			# subsequent calls will just overwrite... new timestamp!
			save_box.push_count = 0
			msg_surf = melfont.render("-- SAVED --", True, PURPLE)
		if len(wordbank) == 0:
			msg_surf = melfont.render("No words!", True, PURPLE)

	# catch switch start / end
	if switch_box.push_count > 0:
		if switching:
			if len(switch_tiles) < 2:
				msg_surf = melfont.render("Pick more!", True, PURPLE)
				pg.mixer.Sound.play(wrong_sound)
			if len(switch_tiles) == 2:	
				# handle matrix switch...
				letterA = board[switch_tiles[0][0]][switch_tiles[0][1]]
				letterB = board[switch_tiles[1][0]][switch_tiles[1][1]]
				board[switch_tiles[0][0]][switch_tiles[0][1]] = letterB
				board[switch_tiles[1][0]][switch_tiles[1][1]] = letterA
				surfA = letter_surfs[switch_tiles[0][0]][switch_tiles[0][1]]
				surfB = letter_surfs[switch_tiles[1][0]][switch_tiles[1][1]]
				letter_surfs[switch_tiles[0][0]][switch_tiles[0][1]] = surfB
				letter_surfs[switch_tiles[1][0]][switch_tiles[1][1]] = surfA
				plusA = plus_surfs[switch_tiles[0][0]][switch_tiles[0][1]]
				plusB = plus_surfs[switch_tiles[1][0]][switch_tiles[1][1]]
				plus_surfs[switch_tiles[0][0]][switch_tiles[0][1]] = plusB
				plus_surfs[switch_tiles[1][0]][switch_tiles[1][1]] = plusA
	
				# then resets
				switch_tiles = []
				switching = False
				del boxes[-1]       # removes switch box... can be re-appended! (assumed always last)
				switch_box.push_count = 0
				switch_box.color = GRAY
				msg_surf = melfont.render("", True, PURPLE)
		else:
			# cover if they try to end switching before picking two
			switching = True
			msg_surf = melfont.render("Choose two!", True, PURPLE)
			switch_box.color = ORANGE


	# clear message in case has ended but still doing last regular draw
	if max_time - overall_time <= 0 and not endgame:
		msg_surf = melfont.render("", True, PURPLE)

	# general drawing, when not paused
	if not pause and not endgame:
		# ~ if in-game and pause button pressed (not because before, false!) ~
		if pause_box.push_count > 0 and newgame:
			pause = True
			cycle_start = time.time()
			pause_curr = pause_1
			pause_box.push_count = 0
		
		screen.fill(WHITE)
		screen.blit(board_img, (0,0))
		for box in boxes:
			if box.push_count > 0:
				# reset boxes now that all handled
				box.push_count = 0
			if box.color != None:   # None used for invisible boxes
				pg.draw.rect(screen, box.color, box.rect, border_radius=box.rounding)
			label_w = box.label.get_width()
			label_h = box.label.get_height()
			x_buffer = 0
			# below just constructs distances to blit label in center of box
			while (x_buffer + label_w/2) <= box.rect.w/2:
				x_buffer = x_buffer + 1
			y_buffer = 0
			while (y_buffer + label_h/2) <= box.rect.h/2:
				y_buffer = y_buffer + 1
			screen.blit(box.label,[box.rect.x + x_buffer,box.rect.y + y_buffer])

		# blit the current message
		screen.blit(msg_surf, [540,689])

		# now current game going drawing stuff
		if newgame:
			# blit all letters on board
			for i in range(0,N):
				for j in range(0,N):
					screen.blit(letter_surfs[i][j], (x_init+(spacing/(2.5))+i*spacing, y_init+(spacing/(2.5))+j*spacing) )
			# blit the scrabble plusses too
			for i in range(0,N):
				for j in range(0,N):
					screen.blit(plus_surfs[i][j], ((spacing/3.5)+x_init+(spacing/(2.5))+i*spacing, (spacing/2.8)+y_init+(spacing/(2.5))+j*spacing) )

			if new_word:
				# need to re-render wordbank surfs
				word_surfs = bank_render(wordbank)
				
			total_width = 0  # track for wrapping!
			y_offset = 0
			num_words = 0
			for word in word_surfs:
				# blit words in bank, but with horizontal wrapping
				print_width = (WIDTH/2)+total_width+num_words*10
				screen.blit(word,[print_width+10,330+y_offset*30])  # 30 is avg height of words
				curr_width = word.get_width()
				total_width = total_width + curr_width
				num_words = num_words + 1
				if total_width > 400:
					total_width = 0
					num_words = 0
					y_offset = y_offset + 1

			# blit switch tile outline squares!
			if switching:
				for tile in switch_tiles:
					screen_coords = [(tile[0]*spacing)+x_init, (tile[1]*spacing)+y_init]
					pg.draw.rect(screen, LIGHTBLUE, pg.Rect(screen_coords[0],screen_coords[1],spacing,spacing),width=7)
			
			# blit the current link
			if not switching:
				for i in range(len(link)):
					screen_coords = [(link[i][0][0]*spacing)+x_init+(spacing)/2, (link[i][0][1]*spacing)+y_init+(spacing)/2]
					if i == 0 and not off_board:
						pg.draw.circle(screen, PURPLE, screen_coords, (spacing)/2 - 5, width=5)
					if i > 0 and not off_board:
						# essentially grabs shited coords, and then picks up/down/diag new coords
						# to draw a line from old -> new, to form the "link" on the board
						last_coords = [(link[i-1][0][0]*spacing)+x_init+(spacing)/2, (link[i-1][0][1]*spacing)+y_init+(spacing)/2]
						mid = [(last_coords[0]+screen_coords[0])/2, (last_coords[1]+screen_coords[1])/2]
						segment_length = 30
						if screen_coords[0] == last_coords[0]:
							start = [mid[0], mid[1]+segment_length]
							end   = [mid[0], mid[1]-segment_length]
						if screen_coords[1] == last_coords[1]:
							start = [mid[0]+segment_length , mid[1]]
							end   = [mid[0]-segment_length , mid[1]]
						if (screen_coords[0] != last_coords[0] and screen_coords[1] != last_coords[1]):
							if last_coords[0] < mid[0]:
								if last_coords[1] < mid[1]:
									start = [mid[0]-segment_length ,mid[1]-segment_length]
									end   = [mid[0]+segment_length ,mid[1]+segment_length]
								if last_coords[1] > mid[1]:
									start = [mid[0]-segment_length ,mid[1]+segment_length]
									end   = [mid[0]+segment_length ,mid[1]-segment_length]
							if last_coords[0] > mid[0]:
								if last_coords[1] < mid[1]:
									start = [mid[0]+segment_length ,mid[1]-segment_length]
									end   = [mid[0]-segment_length ,mid[1]+segment_length]
								if last_coords[1] > mid[1]:
									start = [mid[0]+segment_length ,mid[1]+segment_length]
									end   = [mid[0]-segment_length ,mid[1]-segment_length]
						pg.draw.line(screen, PURPLE, start, end, width=11)
	
			# blit curr score
			curr_score = str(calc_score(wordbank))
			curr_score_surf = midmel.render(curr_score, True, PURPLE)
			screen.blit(score_prefix, [593, 580])
			screen.blit(curr_score_surf, [703,584])

			# current game has ended
			if max_time - overall_time <= 0 or (endgame and not newgame):
				if not endgame:
					clicked = False
					score = str(calc_score(wordbank))
					num_words = str(len(wordbank))
					if len(wordbank) > 0:
						long_w = max(wordbank, key=len)
					else:
						long_w = "N/A"
					# display the score on the frozen game screen
					pg.draw.rect(screen, WHITE, pg.Rect(593,580,300,90))  # cover up curr score !
					show_score(score, num_words, long_w)
					newgame = False
					# now save the score!
					write_score(name, score, num_words)
					# check total word list for all words that are in bank and no in list
					update_totalbank(wordbank)  # couldbecome very long eventually....
					endgame = True

		t_1 = time.time()
		loop_time = t_1 - t_0   # this loop length
		t_0 = time.time()  # start counting again right away!
		overall_time = overall_time + loop_time
	
	if endgame:
		# blit the current message, should be either empty or wordbank saved...
		screen.blit(msg_surf, [540,689])

	# do time variable out here, to totally count passing time?
	if newgame and not pause:
		# update time variable
		curr_time = max_time - overall_time
		loop_c = loop_c + 1
	if not newgame:
		# show just total time inbetween games
		curr_time = max_time

	# blit timer as long as not game over
	if not endgame:
		time_to_render = convert_time(curr_time)
		time_surf = courierfont.render(time_to_render, True, PURPLE)
		screen.blit(time_surf, [310,550])
	
	pg.display.update()
	clock.tick(60)

pg.quit()