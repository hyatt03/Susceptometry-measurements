workdir="$(pwd)"

pm2 delete all

cd $workdir || exit
./start_pm2_webserver.sh

cd $workdir || exit
./start_pm2_cryo_client.sh

cd $workdir || exit
./start_pm2_magnetism_client.sh
