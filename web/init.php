<?php
	require_once __DIR__.'/lib/Twig/Autoloader.php';
	require_once '/usr/share/php/adodb/adodb.inc.php';
	require_once '/usr/share/php/adodb/adodb-exceptions.inc.php';
	require_once __DIR__.'/local_settings.php';

	Twig_Autoloader::register();

	$loader = new Twig_Loader_Filesystem(__DIR__.'/templates/');
	$twig = new Twig_Environment($loader,array(
	//	'cache' => __DIR__.'/cache/'
		'cache' => false,
	));

	$escaper = new Twig_Extension_Escaper(true);
	$twig->addExtension($escaper);

	$db = ADONewConnection('mysql');
	$db->Connect(DB_HOST,DB_USER,DB_PASS,DB_DB) or die('Unable to connect to db');
