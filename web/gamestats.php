<?php
	require_once(__DIR__.'/init.php');

	$res = $db->Execute('
		select sum(numplayers) as numplayers, date
		from server_history
		where status=1 and date > date_sub(now(), interval 7 day)
		group by date
		order by date asc
	');

	$players = array();
	foreach ($res as $cur)
	{
		$players[] = array(
			'val'  => $cur['numplayers'],
			'date' => strtotime($cur['date'])*1000,
		);
	}

	echo $twig->render('gamestats.html',array('players' => $players));
