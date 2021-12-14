#!/usr/bin/python3

import requests
import json
import sys
from discord import Webhook, RequestsWebhookAdapter
import os
import subprocess


# Tautulli
tautulliUrl = 'localhost'
tautulliPort = '8181'
tautulliApiKey = ''

# Discord
discordEnable = True
discordWebhookUrl = ''
discordAvatarUrl = ''
discordUsername = 'Plex Media Server'

# Docker
cleanupEnable = True        #deletes previous docker images if not in use
docker = '/usr/bin/docker'
dockerCompose = '/usr/bin/docker-compose'
composeYaml = '~/docker/plex/docker-compose.yml'


# discord webhook notification
def discordWebhookNotif(message):
    webhook = Webhook.from_url(discordWebhookUrl, adapter=RequestsWebhookAdapter())
    webhook.send(content=message, username=discordUsername, avatar_url=discordAvatarUrl)


# query tautulli API
def tautulliApi(tautulliCmd):
    try:
        r = requests.get("http://{}:{}/api/v2?apikey={}&cmd={}".format(tautulliUrl, tautulliPort, tautulliApiKey, tautulliCmd))
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    
    return r.json()['response']


response = tautulliApi('get_pms_update')
if response['result'] == 'success':
    if(response['data']['update_available']):
        #send notification before starting
        discordWebhookNotif("Plex Media Server version {} is now available. The plex docker container will be restarted to apply this update.".format(response['data']['version'])) if discordEnable

        #retart plex for update
        os.system("{} -f {} pull".format(dockerCompose, composeYaml))
        os.system("{} -f {} stop".format(dockerCompose, composeYaml))
        os.system("{} -f {} up -d".format(dockerCompose, composeYaml))

        #clean up old images
        if cleanupEnable:
            images = subprocess.Popen([docker, 'image', 'ls'], stdout=subprocess.PIPE)
            imgdict = []
            for img in images.stdout:
                line = img.decode('utf-8').rstrip()
                if 'plexinc/pms-docker' in line:
                    imgdict.append(line.split())
            
            for i in imgdict:
                if i[1] != 'latest':
                    os.system("{} image rm {}".format(docker, i[2]))

        #send notification when done
        discordWebhookNotif("Plex Media Server has been updated to version {}".format(response['data']['version'])) if discordEnable
