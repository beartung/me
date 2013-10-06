#Me
It's an internal SNS for employees of same company. Actually, we use this project in :quudouban as there are over 300 people who are not very familiar with each other very well.

#Screen shots

![Home](https://raw.github.com/beartung/me/master/screenshots/screen_shot.png)

#Dependency
mysql

MySQL-python

quixote 1.0

beansdb

redis

juggernaut

wand (http://code.dapps.douban.com/bear/wand.git)

#Run
sudo nginx -c /home/user/me/etc/nginx.conf

gunicorn -w 4 app:app -b 127.0.0.1:8000
