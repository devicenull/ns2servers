<?php
	require_once(__DIR__.'/init.php');

	$res = $db->Execute('
		select srv.id, srv.ip, srv.port, snh.server_name, sh.numplayers, sh.maxplayers, sh.version, sh.status, sh.map
		from servers srv
		left join server_name_history snh on srv.id=snh.id and snh.date_end="0000-00-00 00:00:00"
		left join server_history sh on srv.id=sh.id and srv.last_sample = sh.date
		order by sh.version desc, sh.numplayers desc
	');

	$servers = array();
	foreach ($res as $cur)
	{
		if ($cur['version'] == '')
		{
			$srvinfo = array('numplayers'=>0,'maxplayers'=>0,'map'=>'???','version'=>'','status'=>0);
		}
		else
		{
			$srvinfo = $cur;
		}

		$server_name = $cur['server_name'];
		if ($server_name == '')
		{
			$server_name = '** down **';
		}

		$servers[] = array(
			'id'         => $cur['id'],
			'name'       => $server_name,
			'map'        => $srvinfo['map'],
			'numplayers' => $srvinfo['numplayers'],
			'maxplayers' => $srvinfo['maxplayers'],
			'version'    => $srvinfo['version'],
			'ip'         => $cur['ip'],
			'port'       => $cur['port'],
			'status'     => $srvinfo['status'],
		);
	}

	echo $twig->render('index.html',array('servers' => $servers));
