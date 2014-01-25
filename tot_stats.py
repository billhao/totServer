##
## this module provides method to process the log file generated by tot_server
## Copyright @ totdevteam
##

import sys

class totStats:
	"""collection of stats counters"""
	timestamp = 0
	cnt_login = 0  # num of logins
	cnt_reg = 0    # num of new users
	cnt_usage = 0  # num of usage of the app
	def __init__(self, timestamp):
		self.timestamp = timestamp
		self.cnt_login = 0
		self.cnt_reg = 0
		self.cnt_usage = 0
	def to_str(self):
		str_out = str(self.timestamp) + ' new_user: ' + str(self.cnt_reg) + ' login: ' + str(self.cnt_login) + ' usage: ' + str(self.cnt_usage) + '\n'
		return str_out
		
def processStats(filename):
	try:
		f_open = open(str(filename), "r")
		lines = f_open.readlines()
	except IOError as e:
		print "File I/O error({0}): {1}".format(e.errno, e.strerror)

	stats_list = []  # list of totStats objects. one for each timestamp (day)
	for line in lines:
		words = line.split()
		if len(words) < 7:
			continue # skip a line
		event = words[4]
		if event == "AppRegisterHandler" or event == "AppAuthLoginHandler" or event == "AppUserActHandler":
			timestamp = int(words[1])
			if len(stats_list) == 0:
				the_totStats = totStats(timestamp)
				stats_list.append(the_totStats)
			else:
				if stats_list[len(stats_list)-1].timestamp == timestamp:
					the_totStats = stats_list[len(stats_list)-1]
				else:
					the_totStats = totStats(timestamp)
					stats_list.append(the_totStats)
			if event == "AppRegisterHandler":
				the_totStats.cnt_reg += 1
			elif event == "AppAuthLoginHandler":
				the_totStats.cnt_login += 1
			elif event == "AppUserActHandler":
				the_totStats.cnt_usage += 1
	return stats_list

if __name__ == "__main__":
	print "start processing log file..."
	stats_list = processStats("nohup.out")
	for stat in stats_list:
		print(stat.to_str())
	print "done"
				
					
			
	
	
