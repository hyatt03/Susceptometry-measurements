cd "../web_server" || exit
PYTHONPATH="$(pwd)/.." pm2 start python3 --name susceptometry_server -- "$(pwd)/server.py"
