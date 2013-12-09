from HL2MasterClient import HL2MasterClient
from HL2QueryClient import HL2QueryClient

from twisted.internet import reactor, task

from sqlalchemy import create_engine
from sqlalchemy.sql.expression import text, insert, select, update
from sqlalchemy.sql import and_, or_, not_
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime

import datetime

engine = create_engine('mysql://ns2servers:password@127.0.0.1/ns2servers')
db = engine.connect()

metadata = MetaData()
tbl_servers = Table('servers', metadata,
	Column('id', Integer, primary_key=True),
	Column('ip', String),
	Column('port', Integer),
	Column('last_sample', DateTime),
	)

tbl_server_history = Table('server_history', metadata,
	Column('id', Integer, primary_key=True),
	Column('date', DateTime, primary_key=True),
	Column('map', String(255)),
	Column('numplayers', Integer),
	Column('maxplayers', Integer),
	Column('numbots', Integer),
	Column('password', Integer),
	Column('tickrate', Integer),
	Column('version', Integer),
	Column('status', Integer),
	Column('ent_count', Integer),
)

tbl_server_name_history = Table('server_name_history', metadata,
	Column('id', Integer, primary_key=True),
	Column('date_end', DateTime, primary_key=True),
	Column('date_start', DateTime),
	Column('server_name', String(255)),
)

metadata.create_all(engine)

allTimeouts = {}
numRetries = {}

tm = datetime.datetime.now()

def serverlistCallback(info):
	if info[0] == '0.0.0.0':
		return

	timeout = reactor.callLater(5, lambda:infoTimeout(info))
	serverKey = "%s:%s" % info
	allTimeouts[serverKey] = timeout
	if not serverKey in numRetries:
		numRetries[serverKey] = 3
	qc.startInfoQuery(info)

def getServerId(ip,port):
	res = db.execute(select([tbl_servers],and_(tbl_servers.c.ip==ip,tbl_servers.c.port==port)))
	if res.rowcount == 0:
		res = db.execute(insert(tbl_servers),ip=ip,port=port)
		serverid = res.inserted_primary_key[0]
	else:
		row = res.first();
		serverid = row['id']

	return serverid

def infoCallback(serverinfo):
	serverKey = "%s:%s" % (serverinfo['server_ip'],serverinfo['query_port'])

	if serverKey in allTimeouts:
		allTimeouts[serverKey].cancel()
		del allTimeouts[serverKey]

	if serverKey in numRetries:
		del numRetries[serverKey]

	#print serverinfo

	serverid = getServerId(serverinfo['server_ip'],serverinfo['query_port'])


	serverversion = serverinfo['version']
	if serverversion == '1.0.0.0':
		gd = serverinfo['gamedata'].split('|')
		serverversion = gd[0]

	db.execute(insert(tbl_server_history).prefix_with('IGNORE'),
		id=serverid,
		date=tm,
		map=serverinfo['map'],
		numplayers=serverinfo['numplayers'],
		maxplayers=serverinfo['maxplayers'],
		numbots=serverinfo['numbots'],
		password=serverinfo['password'],
		tickrate=0,
		version=serverversion,
		status=1,
	)

	db.execute(
		update(tbl_servers)
		.where ( tbl_servers.c.id==serverid)
		.values(
			last_sample=tm
		)
	)

	qc.startRulesQuery((serverinfo['server_ip'],serverinfo['query_port']))

	donameinsert = False
	res = db.execute(
			select([tbl_server_name_history],
				and_(
					tbl_server_name_history.c.id==serverid,
					tbl_server_name_history.c.date_end=='0000-00-00 00:00:00'
				)
			)
		)
	if res.rowcount == 0:
		donameinsert = True
	else:
		row = res.first()
		if row['server_name'].lower().strip() != serverinfo['server_name'].lower().strip():
			donameinsert = True
			db.execute(
				update(tbl_server_name_history)
				.where(
					and_(
						tbl_server_name_history.c.id==serverid,
						tbl_server_name_history.c.date_end=='0000-00-00 00:00:00'
					)
				)
				.values(
					date_end=datetime.datetime.now()
				)
			)

	if donameinsert:
		db.execute(insert(tbl_server_name_history),
			id=serverid,
			date_end='0000-00-00 00:00:00',
			date_start=datetime.datetime.now(),
			server_name=serverinfo['server_name'],
		)

def rulesCallback(ip,port,rules):
	serverid = getServerId(ip,port)

	for rule in rules:
		if rule[0] == 'tickrate':
			db.execute(
				update(tbl_server_history)
				.where(
					and_(
						tbl_server_history.c.id==serverid,
						tbl_server_history.c.date==tm,
					)
				)
				.values(
					tickrate=rule[1]
				)
			)
		elif rule[0] == 'ent_count':
			db.execute(
				update(tbl_server_history)
				.where(
					and_(
						tbl_server_history.c.id==serverid,
						tbl_server_history.c.date==tm,
					)
				)
				.values(
					ent_count=rule[1].replace(',','')
				)
			)

def infoTimeout(info):
	print "Server timed out!", info
	serverKey = "%s:%s" % info
	if serverKey in allTimeouts:
		del allTimeouts[serverKey]

	if not serverKey in numRetries or numRetries[serverKey] > 0:
		numRetries[serverKey] -= 1
		serverlistCallback(info)
	else:
		print "Server retry limit reached:",info
		serverid = getServerId(info[0],info[1])
		db.execute(insert(tbl_server_history).prefix_with('IGNORE'),
			id=serverid,
			date=tm,
			status=0,
		)

		db.execute(
			update(tbl_servers)
			.where ( tbl_servers.c.id==serverid)
			.values(
				last_sample=tm
			)
		)

def startServerList():
	global tm
	print "Starting master server query..."
	tm = datetime.datetime.now();

	tm = tm - datetime.timedelta(minutes=tm.minute % 5,
								seconds=tm.second,
								microseconds=tm.microsecond)

	mc.startServerList("208.64.200.39",27011,serverlistCallback, filters="\\gamedir\\naturalselection2\\")


mc = HL2MasterClient()
qc = HL2QueryClient(infoCallback,rulesCallback)

reactor.listenUDP(30233, mc)
reactor.listenUDP(0, qc)


loop1 = task.LoopingCall(lambda:serverlistCallback(('208.64.37.226',27016)))
loop1.start(300)

loop2 = task.LoopingCall(lambda:serverlistCallback(('208.167.244.65',27016)))
loop2.start(300)

loop = task.LoopingCall(startServerList)
loop.start(300)

#reactor.callLater(2,lambda:mc.startServerList("69.28.140.247",27011,filters="\\gamedir\\tf\\"))

reactor.run()
