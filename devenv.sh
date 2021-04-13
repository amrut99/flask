export FLASK_ENV=development
export FLASK_APP=producer.py

#Mongo DB
sudo docker pull mongo

sudo mkdir -p ~/developer/mongodata
sudo docker run -it -v mongodata:/data/db -p 27017:27017 --name mongodb -d mongo

sudo docker exec -it mongodb bash
mongo -host localhost -port 27017 

gunicorn --worker-class eventlet -w 1 module:app