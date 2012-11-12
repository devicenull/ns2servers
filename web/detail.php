<?php
	require_once(__DIR__.'/init.php');

	if (!isset($_REQUEST['date']))
	{
		$date = time();
	}
	else
	{
		$date = strtotime($_REQUEST['date'].' 23:59:59');
		if ($date > time()) $date = time();
	}

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
	$params['date'] = strftime('%D',$date);

	$res = $db->Execute('
		select *
		from server_history
		where id=? and date > date_sub(from_unixtime(?), interval 24 hour) and date < from_unixtime(?)
		order by date asc
	',array($_REQUEST['id'],$date,$date));

	$lastmap = '';
	$lastmapstart = 0;


	$colors = array('4db6bc','368a8f','8bcfd3');
	$i = 0;
	$ticktotals = array();
	$ticksamples = array();
	foreach ($res as $cur)
	{
		$date = strtotime($cur['date'])*1000;
		$params['players'][] = array('val'=>$cur['numplayers'],'date'=>$date);
		$params['tickrate'][] = array('val'=>$cur['tickrate'],'date'=>$date);
		$ticktotals[(int)$cur['numplayers']] += $cur['tickrate'];
		$ticksamples[$cur['numplayers']]++;
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
	ksort($ticktotals);
	unset($ticktotals[0]);
	$params['avgticks'] = array();
	foreach ($ticktotals as $players=>$total)
	{
		$params['avgticks'][] = array('players'=>$players,'avgtick'=>round($total/$ticksamples[$players]));
	}

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
