SET PYTHONPATH="%CD%\.."

cd ..\web_server
call pm2 start python --name susceptometry_server -- "%CD%\server.py"

cd ..\socket_clients
call pm2 start python --name cryo_client -- "%CD%\cryogenics_client.py"
call pm2 start python --name magn_client -- "%CD%\magnetism_client.py"


