source .env/bin/activate
cd api
nohup python flaskr.py > output.log &
echo "started web application..."
echo "\n"
