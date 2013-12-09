from twisted.internet.protocol import DatagramProtocol

from HL2MasterProtocol import HL2MasterProtocol

from dump import dump

class HL2MasterClient(DatagramProtocol):
	# Provide a basic wrapper around HL2MasterProtocol for use with twisted
	# This is a client for the master servers
	def __init__(self,srvinfo=None):
		self.master = HL2MasterProtocol(srvinfo)

	def startHandshake(self,dest_ip,dest_port):
		#print 'Starting master handshake with %s:%i' % (dest_ip,dest_port)
		for cur in self.master.getInitalPacket():
			self.transport.write(cur,(dest_ip,dest_port))

	def startServerList(self,dest_ip,dest_port,callback, region="\xFF",filters=""):
		print 'Retrieving server list for region=%s, filters=%s from %s:%i' % (region,filters,dest_ip,dest_port)
		self.master.setCallback(callback)
		for cur in self.master.getQueryPacket(region,"0.0.0.0:0",filters):
			self.transport.write(cur,(dest_ip,dest_port))

	def datagramReceived(self, data, (host, port)):
		for cur in self.master.handlePacket(data,host,port):
			self.transport.write(cur,(host,port))
