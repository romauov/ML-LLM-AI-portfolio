<?php
function post_request() {
    $url = "http://147.45.105.97:8000/get_qr/";
    $data = json_decode(file_get_contents('example.json'), true);

    $headers = [
        "Content-Type: application/json"
    ];

    $auth = base64_encode('api_user:V7INZ7e_rO');

    $options = [
        'http' => [
            'header'  => [
                "Content-Type: application/json",
                "Authorization: Basic $auth"
            ],
            'method'  => 'POST',
            'content' => json_encode($data),
            'timeout' => 60
        ]
    ];

    $context  = stream_context_create($options);
    $response = file_get_contents($url, false, $context);

    return $response;
}

$response = post_request();
echo $response;
?>
