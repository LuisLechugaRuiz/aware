# Setup

### Supabase migration
supabase db diff --db-url postgresql://postgres:postgres@127.0.0.1:54322/postgres


----

### Conflict between supabase and weaviate

httpx>=0.24,<0.26

and weaviate == 0.26.

Short fix: Adapt weaviate version..


#### NPM Install
npm install mammoth

### RUN REDIS
sudo apt install redis-server
sudo service redis-server start
sudo service redis-server status

### RUN RABBITMQ
sudo systemctl enable rabbitmq-server 
sudo systemctl start rabbitmq-server
sudo systemctl status rabbitmq-server

### Supervisor
sudo apt-get install supervisor

On update needs:
sudo supervisorctl reread
sudo supervisorctl update 
sudo supervisorctl start assistant_worker

#### Restart supervisor
sudo supervisorctl restart all