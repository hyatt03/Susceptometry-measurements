cd "../socket_clients" || exit
PYTHONPATH="$(pwd)/.." pm2 start python3 --name magn_client -- "$(pwd)/magnetism_client.py"
