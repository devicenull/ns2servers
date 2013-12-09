import struct, random

from socket import ntohs, htons

from dump import dump

class HL2MasterProtocol:
	# Provide an implementation of the HL2 Master server protocol
	CHALLENGE_REQUEST = "q" # client -> server
	CHALLENGE_RESPONSE = "\xFF\xFF\xFF\xFF\x73\x0A" # server -> client
	HANDSHAKE_REQUEST = "0\x0a" # client -> server
	OUT_OF_DATE_RESPONSE = "\xFF\xFF\xFF\xFF\x4F" # server -> client
	PRINT_REQUEST = "l" # client -> server (chr(108))

	SERVERLIST_REQUEST = "1" # client -> server
	SERVERLIST_RESPONSE = "\xFF\xFF\xFF\xFF\x66\x0A" # server -> client

	QUIT_REQUEST = "\x62\xAA\x00" # client -> server


	def __init__(self,srvinfo=None,srvlist=None):
		self.req_region="\xFF"
		self.req_filters = ""
		self.srv = srvinfo
		self.srvlist = srvlist

	def getInitalPacket(self):
		return [self.CHALLENGE_REQUEST]

	def getQueryPacket(self,region="\xFF",startip="",filters=""):
		self.req_region = region
		self.req_filters = filters
		return [self._buildQueryRequest(region,startip,filters)]

	def setCallback(self, callback):
		self.callback = callback

	def handlePacket(self,data,src_ip,src_port=-1):
		# "client" requests
		if len(data) > 6 and data[0:6] == self.CHALLENGE_RESPONSE:
			#print 'Sending master response to %s:%i' % (src_ip,src_port)
			return [self._buildHandshakeRequest(struct.unpack("I",data[6:10]))]

		elif len(data) > 6 and data[0:6] == self.SERVERLIST_RESPONSE:
			print 'Got server list response'
			#print dump(data)
			for i in range(6,len(data),6):
				info = self._readIP(data[i:i+6])
				self.callback(info)
				last = info
			if last[0] != "0.0.0.0" and last[1] != 0:
				return [self._buildQueryRequest(self.req_region,"%s:%i" % (last[0],last[1]),self.req_filters)]
			else:
				return []

		elif len(data) >= 5 and data[0:5] == self.OUT_OF_DATE_RESPONSE:
			print 'Server out of date, increasing version from %i' % (self.srv.netversion)
			self.srv.netversion += 1

		# "server" requests
		elif len(data) == 1 and data[0] == self.CHALLENGE_REQUEST:
			challenge = random.getrandbits(32)
			print 'Got challenge request from %s:%i, sending challenge %i' % (src_ip,src_port,challenge)
			self.srvlist.setChallenge(src_ip,src_port,challenge)
			return [self._buildChallengeResponse(challenge)]

		elif len(data) > 2 and data[0:2] == self.HANDSHAKE_REQUEST:
			print 'Got handshake packet from %s:%i' % (src_ip,src_port)
			args = self._readSlashedQuery(data[2:-1])
			print args

			# FIXME: ignore response until we know sucess/failure codes
			self.srvlist.handshake(src_ip,src_port,args)

		elif len(data) == 1 and data[0] == self.SERVERLIST_REQUEST:
			print 'Got serverlist request from %s:%i' % (src_ip,src_port)
			region = data[1]
			args = data[2:].split("\x00")
			startip = args[0]
			filters = self._readSlashedQuery(args[1])

			# FIXME: just assume we don't have enough servers to fill the list for now
			servers = self.srvlist.getServerList(region,filters)
			packet = ""

		elif len(data) == 3 and data == self.QUIT_REQUEST:
			print 'Got quit request from %s:%i' % (src_ip,src_port)
			self.srvlist.quit(src_ip,src_port)

		return []

	# read an IP/port from a packet
	def _readIP(self,data):
		ipstruct = struct.unpack("BBBBH",data)
		ip = "%i.%i.%i.%i" % (ipstruct[0],ipstruct[1],ipstruct[2],ipstruct[3])
		port = ntohs(ipstruct[4])
		return (ip,port)

	# Prepare an IP/port combo to be written to a packet
	def _writeIP(self,ip,port):
		octets = ip.split(".")
		return struct.pack("BBBBH",octets[0],octets[1],octets[2],octets[3],htons(port))

	# handle the \\name\\value format
	# return a dict containing name:value pairs
	def _readSlashedQuery(self,query):
		spl = query.split("\\")
		args = {}
		for i in range(1,len(spl),2):
			args[spl[i]] = spl[i+1]
		return args

	def _buildQueryRequest(self,region="\xFF",startip="0.0.0.0:0",filters=""):
		packet = self.SERVERLIST_REQUEST
		packet += region
		packet += "%s\x00" % (startip)
		packet += "%s\x00" % (filters)
		return packet

	def _buildHandshakeRequest(self,challenge):
		packet = self.HANDSHAKE_REQUEST
		packet += "\\protocol\\%i" % (self.srv.netversion)
		packet += "\\challenge\\%s" % (challenge)
		packet += "\\players\\%i" % (len(self.srv.players))
		packet += "\\max\\%i" % (self.srv.maxplayers)
		packet += "\\bots\\0"
		packet += "\\gamedir\\%s" % (self.srv.gamedir)
		packet += "\\map\\%s" % (self.srv.mapname)
		packet += "\\password\\%i" % (self.srv.password)
		packet += "\\os\\%s" % (self.srv.os)
		packet += "\\lan\\%i" % (self.srv.lan)
		packet += "\\region\\%i" % (self.srv.region)
		#packet += "\\gametype\\%s" % (self.srv.mapname[:self.srv.mapname.find("_")])
		packet += "\\type\\%s" % (self.srv.dedicated)
		packet += "\\secure\\%i" % (self.srv.secure)
		packet += "\\version\\%s" % (self.srv.version)
		packet += "\\product\\%s" % (self.srv.gamedir)
		packet += "\x0a"
		return packet

	def _buildChallengeResponse(self,challenge):
		packet = self.CHALLENGE_RESPONSE
		packet += "%s" % struct.pack("I",challenge)
		return packet
