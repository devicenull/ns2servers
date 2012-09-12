<?php
	require_once(__DIR__.'/init.php');

	$res = $db->Execute('
		select srv.id, srv.ip, srv.port, snh.server_name
		from servers srv
		left join server_name_history snh on srv.id=snh.id and snh.date_end="0000-00-00 00:00:00"
		where srv.id=?
	',array($_REQUEST['id']));

	$params = array('plotbands'=>array(),'players'=>array(),'tickrate'=>array(),'ent_count'=>array());
	$params['id'] = $res->fields['id'];
	$params['ip'] = $res->fields['ip'];
	$params['port'] = $res->fields['port'];
	$params['server_name'] = $res->fields['server_name'];

	$res = $db->Execute('
		select *
		from server_history
		where id=? and date > date_sub(now(), interval 24 hour)
		order by date asc
	',array($_REQUEST['id']));

	$lastmap = '';
	$lastmapstart = 0;


	$colors = array('4db6bc','368a8f','8bcfd3');
	$i = 0;
	foreach ($res as $cur)
	{
		$date = strtotime($cur['date'])*1000;
		$params['players'][] = array('val'=>$cur['numplayers'],'date'=>$date);
		$params['tickrate'][] = array('val'=>$cur['tickrate'],'date'=>$date);
		$params['ent_count'][] = array('val'=>$cur['ent_count'],'date'=>$date);
		if ($cur['map'] != $lastmap)
		{
			if ($lastmapstart > 0)
			{
				$params['plotbands'][] = array(
					'start' => $lastmapstart,
					'end'   => $date,
					'map'   => $lastmap,
					'color' => $colors[$i%count($colors)],
				);
			}
			$lastmap = $cur['map'];
			$lastmapstart = $date;
			$i++;

		}
	}
	$params['plotbands'][] = array(
		'start' => $lastmapstart,
		'end'   => $date,
		'map'   => $lastmap,
		'color' => $colors[$i%count($colors)],
	);

	$res = $db->Execute('
		select *
		from server_name_history
		where id=?
		order by date_end desc
	',array($_REQUEST['id']));
	foreach ($res as $cur)
	{
		$params['names'][] = array(
			'start' => $cur['date_start'],
			'end' => $cur['date_end'],
			'name' => $cur['server_name'],
		);
	}

	echo $twig->render('detail.html',$params);