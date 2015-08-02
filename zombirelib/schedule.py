import threading
import datetime
import time
import random
import math

class Schedule:
	loop = True
	is_bonus_on = False
	last_hour_mp = -1
	last_hour_bonus = -1
	bonus_vars = []
	bonus_texts = ("The following players found \x02{}\x02. Upon consuming it, they temporarily gained \x0230%\x02 boost on attack/defense: ", 
		"The following players \x02{}\x02. Due to that, they temporarily lost \x0230%\x02 of their attack/defense: ")
	bonus_vars.append(("a Red Bull", "a Mega Potion", "Elixir", "a Super Vaccine", 
		"a delicious Honeypot", "a Rainbow Cake"))
	bonus_vars.append(("caught swine flu", "got bitten by a venomous snake", "got stinged by a wasp", 
		"got attacked by a wolf", "suffered from Vitamin C deficiency"))

	def __init__(self, conn, dbc, channel, players):
		random.seed()
		self.connection = conn
		self.dbc = dbc
		self.channel = channel
		self.players = players
		regenerate_thread = threading.Thread(target=self.regenerate_mp)
		regenerate_thread.start()
		bonus_thread = threading.Thread(target=self.give_bonus)
		bonus_thread.start()

	def regenerate_mp(self):
		while self.loop:
			if self.players:
				now_hour = datetime.datetime.now().hour
				now_min = datetime.datetime.now().minute
				now_sec = datetime.datetime.now().second
				if now_min == 0 and now_sec >= 0 and now_sec < 6 and self.last_hour_mp != now_hour:
					self.last_hour_mp = now_hour
					for nick in self.players:
						self.players[nick]['mp'] = self.players[nick]['mmp']
					self.connection.privmsg(self.channel, "\x02One hour has passed, " +
						"and all players have their MP regenerated.\x02")
			time.sleep(5)

	def give_bonus(self):
		while self.loop:
			if len(self.players) > 1:
				now_hour = datetime.datetime.now().hour
				now_min = datetime.datetime.now().minute
				now_sec = datetime.datetime.now().second
				if now_min == 1 and now_sec >= 0 and now_sec < 10 and self.last_hour_bonus != now_hour:
					self.last_hour_bonus = now_hour
					if self.is_bonus_on:
						self.connection.privmsg(self.channel, "Bonus temporary effects have now disappeared.")
						self.clear_bonus()
						self.is_bonus_on = False
					if now_hour % 3 == 0: #every 3 hours
						# types of bonuses: 0 for nothing, 1 for +30%, 2 for -30%, 3 for 1 & 2
						# probab of choosing bonuses: 0: 10%, 1: 40%, 2: 40%, 3: 10%
						bonus_types = [0] + [1] * 4 + [2] * 4 + [3]
						bonus_choice = random.choice(bonus_types)
						if bonus_choice in (1, 2):
							self.is_bonus_on = True
							list_nicks = self.bonus_random_players(bonus_choice)
							self.connection.privmsg(self.channel, self.bonus_texts[bonus_choice - 1].
								format(random.choice(self.bonus_vars[bonus_choice - 1])))
							self.connection.privmsg(self.channel, "\x02" + list_nicks + "\x02")
						elif bonus_choice == 3:
							self.is_bonus_on = True
							[list_nicks1, list_nicks2] = self.bonus_random_players(3)
							self.connection.privmsg(self.channel, self.bonus_texts[0].format(
								random.choice(self.bonus_vars[0])))
							self.connection.privmsg(self.channel, "\x02" + list_nicks1 + "\x02")
							self.connection.privmsg(self.channel, self.bonus_texts[1].format(
								random.choice(self.bonus_vars[1])))
							self.connection.privmsg(self.channel, "\x02" + list_nicks2 + "\x02")
						else:
							pass # no bonus
					# save new stats after regenerate_mp and give_bonus
					self.dbc.save(self.players)
			time.sleep(5)

	def bonus_random_players(self, btype):
		nb_sample = math.ceil(0.1 * len(self.players))
		if btype in (1, 2):
			rand_sample = random.sample(list(self.players), nb_sample)
			list_nicks = ", ".join(rand_sample)
			for nick in rand_sample:
				self.players[nick]['bonus'] += btype
			return list_nicks
		else: # btype == 3
			half1 = random.sample(list(self.players), len(self.players) // 2)
			half2 = [nick for nick in self.players if nick not in half1]
			rand_sample1 = random.sample(half1, nb_sample)
			rand_sample2 = random.sample(half2, nb_sample)
			list_nicks1 = ", ".join(rand_sample1)
			list_nicks2 = ", ".join(rand_sample2)
			for nick in rand_sample1:
				self.players[nick]['bonus'] += 1
			for nick in rand_sample2:
				self.players[nick]['bonus'] += 2
			return [list_nicks1, list_nicks2]

	def clear_bonus(self):
		for nick in self.players:
			old_val = self.players[nick]['bonus']
			self.players[nick]['bonus'] = (old_val // 10) * 10

	def stop(self):
		self.loop = False
