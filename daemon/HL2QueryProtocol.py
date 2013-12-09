import struct, random

from dump import dump

class HL2QueryProtocol:
	# This is an implemenation of the HL2 Query protocol, and is designed to operate as a server
	# not as a client
	MAX_DATA = 1248
	A2S_INFO_RESPONSE = 'I'
	A2A_PING_RESPONSE = 'j'
	A2S_PLAYER_RESPONSE = 'D'
	A2S_RULES_RESPONSE = 'E'
	A2S_CHALLENGE_RESPONSE = 'A'

	def __init__(self,srvinfo,callback,rulesCallback):
		self.srv = srvinfo
		self.ping = 0
		self.challenge = 0
		self.info = 0
		self.player = 0
		self.rules = 0
		self.callback = callback
		self.rulesCallback = rulesCallback

	def handlePacket(self,data,src_ip,src_port=-1):
		if len(data) < 5:
			return []
		if data[4] == 'i':
			# A2A_PING
			#print 'Got A2A_PING from %s:%i' % (src_ip,src_port)
			self.ping += 1
			return self._createResponse(self.A2A_PING_RESPONSE,"")
		elif data[4] == '\x57':
			# A2S_SERVERQUERY_GETCHALLENGE
			#print 'Got A2S_SERVERQUERY_GETCHALLENGE from %s:%i' % (src_ip,src_port)
			self.challenge += 1
			return self._createResponse(self.A2S_CHALLENGE_RESPONSE,struct.pack("i",random.randint(2,999999)))
		elif data[4] == 'T':
			# A2S_INFO
			#print 'Got A2S_INFO from %s:%i' % (src_ip,src_port)
			self.info += 1
			return self._createResponse(self.A2S_INFO_RESPONSE,self._getInfoData())
		elif data[4] == '\x55':
			# A2S_PLAYER
			#print 'Got A2S_PLAYER from %s:%i' % (src_ip,src_port)
			if len(data) < 9:
				print 'not enough data'
				return []
			if (struct.unpack("i",data[5:9]) == -1):
				self.challenge += 1
				return self._createResponse(self.A2S_CHALLENGE_RESPONSE,struct.pack("i",random.randint(2,999999)))
			self.player += 1
			return self._createResponse(self.A2S_PLAYER_RESPONSE,self._getPlayerData())
		elif data[4] == '\x56':
			# A2S_RULES
			#print 'Got A2S_RULES from %s:%i' % (src_ip,src_port)
			if len(data) < 9:
				print 'not enough data'
				return []
			if (struct.unpack("i",data[5:9]) == -1):
				self.challenge += 1
				return self._createResponse(self.A2S_CHALLENGE_RESPONSE,struct.pack("i",random.randint(2,999999)))
			self.rules += 1
			return self._createResponse(self.A2S_RULES_RESPONSE,self._getRulesData())
		elif data[4] == HL2QueryProtocol.A2S_INFO_RESPONSE:
			#print "got info packet"
			#print dump(data)
			serverinfo = self.parseInfoPacket(src_ip,src_port,data)
			self.callback(serverinfo)
		elif data[4] == HL2QueryProtocol.A2S_CHALLENGE_RESPONSE:
			#print "got challenge response"
			return self.getRulesPacket(data[5:])
		elif data[4] == HL2QueryProtocol.A2S_RULES_RESPONSE:
			#print "got rules response"
			rules = self.parseRulesPacket(data)
			self.rulesCallback(src_ip,src_port,rules)
		else:
			print "got invalid packet"
			print dump(data)

		return []

	def parseInfoPacket(self,src_ip,src_port,data):
		curpos = 5
		netversion = ord(data[curpos])
		curpos += 1
		servername = self._readString(data,curpos)
		curpos += len(servername) + 1

		mapname = self._readString(data,curpos)
		curpos += len(mapname) + 1

		gamedir = self._readString(data,curpos)
		curpos += len(gamedir) + 1

		gamename = self._readString(data,curpos)
		curpos += len(gamename) + 1

		(appid,) = struct.unpack('h',data[curpos:curpos+2])
		curpos += 2


		(numplayers,maxplayers,numbots,dedicated,os,password,vac) = struct.unpack('ccccccc',data[curpos:curpos+7])
		numplayers = ord(numplayers)
		maxplayers = ord(maxplayers)
		numbots = ord(numbots)
		password = ord(password)
		vac = ord(vac)
		curpos += 7

		version = self._readString(data,curpos)
		curpos += len(version) + 1

		edf = ord(data[curpos])
		curpos += 1

		serverdata = {
			'netversion': netversion,
			'server_name': servername,
			'map': mapname,
			'gamedir': gamedir,
			'gamedesc': gamename,
			'appid': appid,
			'numplayers': numplayers,
			'maxplayers': maxplayers,
			'numbots': numbots,
			'dedicated': dedicated,
			'os': os,
			'password': password,
			'vac': vac,
			'version': version,
			'server_ip': src_ip,
			'query_port': src_port,
		}

		if edf & 0x80:
			(port,) = struct.unpack('h',data[curpos:curpos+2])
			curpos += 2
			serverdata['port'] = port

		if edf & 0x10:
			(steamid,) = struct.unpack('q',data[curpos:curpos+8])
			curpos += 8
			serverdata['steamid'] = steamid

		if edf & 0x40:
			spectator = self._readString(data,curpos)
			curpos += len(spectator) + 1
			serverdata['spectator'] = spectator

		if edf & 0x20:
			gamedata = self._readString(data,curpos)
			curpos += len(gamedata) + 1
			serverdata['gamedata'] = gamedata

		if edf & 0x01:
			(gameid,) = struct.unpack('q',data[curpos:curpos+8])
			curpos += 8
			serverdata['gameid'] = gameid

		#print serverdata
		return serverdata


	def parseRulesPacket(self,data):
		curpos = 5

		# We don't really care about numrules.. just ignore it and start looking for rules pairs
		(numrules,) = struct.unpack('h',data[curpos:curpos+2])
		curpos += 2

		rules = []
		while curpos < len(data):
			rulename = self._readString(data,curpos)
			curpos += len(rulename) + 1
			rulevalue = self._readString(data,curpos)
			curpos += len(rulevalue) + 1
			rules.append((rulename,rulevalue))

		return rules

	def _readString(self,data,curpos):
		stringend = data[curpos:].find("\x00")
		return data[curpos:curpos+stringend]

	def getStats(self):
		return {'ping':self.ping,'chal':self.challenge,'info':self.info,'player':self.player,'rules':self.rules}

	def _createResponse(self,responseCode,data):
		curpos = 0
		ret = []
		while curpos < len(data):
			end = curpos+self.MAX_DATA
			if curpos+end > len(data):
				end = len(data)

			buf = "\xFF\xFF\xFF\xFF%c" % responseCode
			buf += data[curpos:end]
			ret.append(buf)
			curpos = end
		return ret

	def _getInfoData(self):
		buf = struct.pack("B",self.srv.netversion)
		buf += "%s\x00" % self.srv.servername
		buf += "%s\x00" % self.srv.mapname
		buf += "%s\x00" % self.srv.gamedir
		buf += "%s\x00" % self.srv.gamedesc
		buf += struct.pack("hBBBcccc"
				,self.srv.appid
				,len(self.srv.players)
				,self.srv.maxplayers
				,0 # bots
				,self.srv.dedicated
				,self.srv.os
				,chr(self.srv.password)
				,chr(self.srv.secure)
				)
		buf += "%s\x00" % self.srv.version
		#buf += struct.pack("c",chr(self.srv.edf))
		return buf

	def _getPlayerData(self):
		buf = struct.pack("B",len(self.srv.players))
		# we need to keep track of i anyway, so just use this kind of loop
		for i in range(0,len(self.srv.players)):
			buf += struct.pack("B",i)
			buf += "%s\x00" % self.srv.players[i]['name']
			buf += struct.pack("lf",self.srv.players[i]['kills'],self.srv.players[i]['time'])
		return buf

	def _getRulesData(self):
		buf = struct.pack("h",len(self.srv.rules))
		for cur in self.srv.rules:
			buf += "%s\x00" % cur['rule']
			buf += "%s\x00" % cur['value']
		return buf

	def getInfoPacket(self):
		return ["\xFF\xFF\xFF\xFFTSource Engine Query\x00"]

	def getRulesPacket(self,challenge="\xFF\xFF\xFF\xFF"):
		return ["\xFF\xFF\xFF\xFF\x56%s" % challenge]