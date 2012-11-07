<?php
	require(__DIR__.'/../web/init.php');

	$removeservers = $totalservers = 0;

	$res = $db->Execute('select * from servers');
	foreach ($res as $cur)
	{
		$res2 = $db->Execute('select * from server_history where id=? and status=1 order by date desc limit 1',array($cur['id']));

		$delete = false;
		if ($res2->RecordCount() == 0)
		{
			echo "Found no results for server {$cur['id']}\n";
			$removeservers++;
			$delete = true;
		}
		else if (time()-strtotime($res2->fields['date']) > 24*60*60)
		{
			echo "{$cur['id']} last sample was on {$res2->fields['date']}\n";
			$removeservers++;
			$delete = true;
		}

		if ($delete)
		{
			$db->Execute('delete from server_history where id=?',array($cur['id']));
			$db->Execute('delete from server_name_history where id=?',array($cur['id']));
			$db->Execute('delete from servers where id=?',array($cur['id']));
		}
		$totalservers++;
	}

	echo "Remove {$removeservers}/{$totalservers}\n";
