#!/usr/bin/python3

import requests
import sys
from discord import Webhook, RequestsWebhookAdapter
import os
import subprocess


########################
# --- BEGIN CONFIGS -- #
#

# Tautulli Config
tautulliUrl = 'tautulli.local'
tautulliPort = '8181'
tautulliApiKey = ''

# Discord Config
webhookUrl = ''
avatarUrl = ''
username = 'Plex Media Server (Tautulli)'

# Updatable containers
contlist = {
        'plex': {
            'tautulliCmd': 'get_pms_update',
            'discord_message_label': 'Plex Media Server',
            'update_available_label': 'update_available',
            'update_version_label': 'version',
            'docker_compose_file': '',
            'docker_image': 'plexinc/pms-docker'
        },
        'tautulli': {
            'tautulliCmd': 'update_check',
            'discord_message_label': 'Tautulli',
            'update_available_label': 'update',
            'update_version_label': 'latest_release',
            'docker_compose_file': '',
            'docker_image': 'tautulli/tautulli'
        },
    }

#
# --- END CONFIGS -- #
######################


# Print usage statement if container name is missing
def usage(exit_code=0):
    print("Must specify container name [plex, tautulli].")
    exit(exit_code)


###
# Get container name as command line arg
try:
    container = sys.argv[1]
except:
    usage(1)


###
# Get update availability from Tautulli API
try:
    r = requests.get("http://{}:{}/api/v2?apikey={}&cmd={}".format(tautulliUrl, tautulliPort, tautulliApiKey, contlist[container]['tautulliCmd']))
except requests.exceptions.RequestException as e:
    raise SystemExit(e)

response = r.json()['response']
print(response)


###
# Pull docker image and restart if there's an update available
if response['result'] == 'success':
    if(response['data'][contlist[container]['update_available_label']]):
        #send notification before starting
        webhook = Webhook.from_url(webhookUrl, adapter=RequestsWebhookAdapter())
        message = "{} version {} is now available. The {} docker container will be restarted to apply this update.".format(contlist[container]['discord_message_label'], response['data'][contlist[container]['update_version_label']], container)
        webhook.send(content=message, username=username, avatar_url=avatarUrl)

        #retart container for update
        os.system("/usr/bin/docker-compose -f {} pull".format(contlist[container]['docker_compose_file']))
        os.system("/usr/bin/docker-compose -f {} stop".format(contlist[container]['docker_compose_file']))
        os.system("/usr/bin/docker-compose -f {} up -d".format(contlist[container]['docker_compose_file']))

        #clean up old images
        images = subprocess.Popen(['/usr/bin/docker', 'image', 'ls'], stdout=subprocess.PIPE)
        imgdict = []
        for img in images.stdout:
            line = img.decode('utf-8').rstrip()
            if contlist[container]['docker_image'] in line:
                imgdict.append(line.split())

        for i in imgdict:
            if i[1] != 'latest':
                os.system("/usr/bin/docker image rm {}".format(i[2]))

        #send notification when done
        message = "{} has been updated to version {}".format(contlist[container]['discord_message_label'], response['data'][contlist[container]['update_version_label']])
        webhook.send(content=message, username=username, avatar_url=avatarUrl)
