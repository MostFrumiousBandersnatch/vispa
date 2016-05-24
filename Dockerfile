FROM        ubuntu:14.04
RUN         apt-get update && apt-get install -y redis-server python-pip
RUN         pip install virtualenv
RUN         mkdir /opt/minichat /opt/minichat/env /opt/minichat/srv /opt/minichat/cli
COPY        requirements.txt /opt/minichat
RUN         virtualenv -p python3 /opt/minichat/env
RUN         /opt/minichat/env/bin/pip install --requirement /opt/minichat/requirements.txt
COPY        srv /opt/minichat/srv
COPY        cli /opt/minichat/cli
EXPOSE      8888
ENTRYPOINT  service redis-server start && /opt/minichat/env/bin/python  /opt/minichat/srv/webapp.py

