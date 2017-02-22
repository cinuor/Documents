#!/usr/bin/python
import requests
import json
import datetime

USER_NAME = 'midea-experience'
PASSWORD = 'Midea_experience!)'
USER_ID = '1c509d89edcc4e9fb97faaca19732323'
PROJECT_ID = '8c06776a9b3143399675f1a19381c387'
VOLUME_ID = '8eddce6a-76d6-4536-82e8-9e6dbb93beb1'
SNAPSHOT_PREFIX = 'gongyinglian_svn'
TIME_DIFFERENCE = 15

#create new snapshot
def get_user_token(user_id, password, project_id):
    url = 'http://10.17.0.39:35357/v3/auth/tokens'
    headers = {'Content-Type':'application/json'}
    payload = {
        'auth': {
            'identity': {
                'methods': ['password'],
                'password': {
                    'user': {'id': user_id,'password': password}
                }
            },
            'scope': {
                'project': {'id': project_id}
            }
        }
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 201:
        return resp.headers['X-Subject-Token']

def backup_volume(project_id, volume_id, X_Auth_Token):
    snapshot_name = get_snapshot_name()
    url = 'http://10.17.0.39:8776/v2/'+project_id+'/snapshots'
    headers = {
        'Content-Type':'application/json',
        'Accept':'application/json',
        'X-Auth-Token': X_Auth_Token
    }
    payload = {
        'snapshot': {
            'display_name': snapshot_name,
            'force': True,
            'display_description': None,
            'volume_id': volume_id
        }
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    result = json.dumps(resp.text)
    if resp.status_code == 202:
        print '%s: success to create new snapshot' %(get_current_time())
        return True
    else:
        print '%s: fail to create new snapshot' %(get_current_time())
        print resp.text
        return False

def get_snapshot_name():
    return SNAPSHOT_PREFIX+'_'+datetime.datetime.now().strftime('%Y%m%d')
###############################################################################



#delete old snapshots
def get_all_snapshots(project_id, X_Auth_Token):
    url = 'http://10.17.0.39:8776/v2/'+project_id+'/snapshots'
    headers = {
        'Accept':'application/json',
        'X-Auth-Token': X_Auth_Token
    }
    resp = requests.get(url, headers=headers)
    snapshots = resp.json()
    return snapshots['snapshots']

def get_time_difference(utc_created_at):
    dot = utc_created_at.rfind('.')
    local_created_at = utc_created_at[:dot]
    created_at = datetime.datetime.strptime(local_created_at,'%Y-%m-%dT%H:%M:%S')
    now = datetime.datetime.now()
    
    return (now-created_at).days

def delete_old_snapshot(project_id, X_Auth_Token):
    snapshots = get_all_snapshots(project_id, X_Auth_Token)
    for snapshot in snapshots:
        time_diff = get_time_difference(snapshot['created_at'])
        if time_diff < TIME_DIFFERENCE:
            continue
        delete_snapshot(project_id, snapshot['id'], X_Auth_Token)

def delete_snapshot(project_id, snapshot_id, X_Auth_Token):
    url = 'http://10.17.0.39:8776/v2/'+project_id+'/snapshots/'+snapshot_id
    headers = {
        'Accept':'application/json',
        'X-Auth-Token': X_Auth_Token
    }
    resp = requests.delete(url, headers=headers)
    if resp.status_code == 202:
        print '%s: success to delete old snapshot %s' %(get_current_time(), snapshot_id)
    else:
        print '%s: fail to delete old snapshot %s' %(get_current_time(),snapshot_id)
        print resp.text
####################################################################################

def get_current_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    X_Auth_Token = get_user_token(USER_ID, PASSWORD, PROJECT_ID)
    done = backup_volume(PROJECT_ID, VOLUME_ID, X_Auth_Token)
    if done:
        delete_old_snapshot(PROJECT_ID, X_Auth_Token)
    else:
        print '%s: fail to create new snapshot, skip deleting old snapshot' %(get_current_time(),)