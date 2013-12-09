from HL2MasterClient import HL2MasterClient
from HL2QueryClient import HL2QueryClient

from twisted.internet import reactor, task

import datetime

def serverlistCallback(info):
	if info[0] == '0.0.0.0':
		return

	print "Server: %s:%s" % info

def startServerList():
	global tm
	print "Starting master server query..."
	tm = datetime.datetime.now();

	tm = tm - datetime.timedelta(minutes=tm.minute % 5,
								seconds=tm.second,
								microseconds=tm.microsecond)


	#mc.startServerList("208.64.200.39",27011,serverlistCallback, filters="\\gamedir\\naturalselection2\\")
	mc.startServerList("208.64.200.39",27011,serverlistCallback, filters="\\gamedir\\naturalselection2\\")

mc = HL2MasterClient()

reactor.listenUDP(30234, mc)


loop = task.LoopingCall(startServerList)
loop.start(300)


reactor.run()
