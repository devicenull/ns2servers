from twisted.internet.protocol import DatagramProtocol

from HL2QueryProtocol import HL2QueryProtocol

from dump import dump

class HL2QueryClient(DatagramProtocol):
	# Provide a basic wrapper around HL2QueryProtocol for use with twisted

	def __init__(self,callback,rulesCallback):
		self.query = HL2QueryProtocol(None,callback,rulesCallback)

	def startInfoQuery(self,srvinfo):
		for cur in self.query.getInfoPacket():
			self.transport.write(cur, srvinfo)

	def datagramReceived(self, data, (host, port)):
		for cur in self.query.handlePacket(data,host,port):
			self.transport.write(cur,(host,port))

	def startRulesQuery(self,srvinfo):
		for cur in self.query.getRulesPacket():
			self.transport.write(cur, srvinfo)