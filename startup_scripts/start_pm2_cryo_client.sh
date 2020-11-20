cd "../socket_clients" || exit
PYTHONPATH="$(pwd)/.." pm2 start python3 --name cryo_client -- "$(pwd)/cryogenics_client.py"
