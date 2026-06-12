
Деплой gitlab-runner
```sh
cd deploy
cp path-to-id_rsa ./server_id_rsa
chmod 600 ./server_id_rsa
ansible-playbook -i hosts deploy.yml
```

Доступ для docker register auth
```commandline
printf "my_username:my_password" | openssl base64 -A
```