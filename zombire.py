#!/usr/bin/env python3

#    Zombire IRC game bot
#    Copyright (C) 2015  Linostar <linux.anas@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import re

import yaml
import irc.bot
import irc.strings

import user_command, admin_command
from db_access import Database

class Zombire(irc.bot.SingleServerIRCBot):
	def __init__(self, config_file):
		self.read_config(config_file)
		self.dbc = Database(self.config)
		self.players = self.dbc.get_players()
		irc.bot.SingleServerIRCBot.__init__(self, [(self.config['server'], self.config['port'])],
		self.config['nick'], self.config['realname'])
		self.uc = user_command.UserCommand(self.connection, self.dbc, self.config['channel'])
		self.ac = admin_command.AdminCommand(self.connection, self.dbc, self.config['admin_passwd'])

	def read_config(self, filename):
		if not os.path.exists(filename):
			print('Error: config.yml cannot be found.')
			sys.exit(1)
		with open(filename, 'r') as config_fd:
			self.config = yaml.load(config_fd)

	def on_welcome(self, c, e):
		if self.config['nspass']:
			self.connection.privmsg("nickserv", "identify {}".format(self.config['nspass']))
		c.join(self.config['channel'])

	def on_privnotice(self, c, e):
		# checking for nickserv replies
		args = e.arguments[0].lower()
		if e.source.nick.lower() == "nickserv" and args.startswith("status "):
			largs = args.split(" ")
			if largs[2] == "3": # if user is identified to nickserv 
				self.uc.register2(largs[1], self.players) # proceed with the registration
			return

	def on_privmsg(self, c, e):
		detected = re.match(r"admin\s+(.+)", e.arguments[0], re.IGNORECASE)
		if detected:
			self.ac.execute(e, detected.group(1).strip(), self.players)
			return

	def on_pubmsg(self, c, e):
		re_exprs = (r"\!(register)", r"\!(unregister)", r"\!(status\s+.+)",
			r"\!(attack\s+.+)", r"\!(assist\s+.+)")
		for expr in re_exprs:
			try:
				detected = re.match(expr, e.arguments[0], re.IGNORECASE)
				raise DetectedException
			except DetectedException:
				if detected:
					self.uc.execute(e, detected.group(1).strip(), self.players)
					return


class DetectedException(Exception):
	def __init__(self, value=None):
		self.value = value

	def __str__(self):
		return repr(self.value)


def main():
	print("Zombire bot is running. To stop the bot, press Ctrl+C.")
	bot = Zombire("config.yml")
	bot.start()

if __name__ == "__main__":
	main()
