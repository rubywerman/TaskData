import requests 
import json 
import time
import boto3

volunteers = {}
CACHE_FILENAME = "curr.txt"
i = 0
r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))

cap = 1000 #adding cap for testing purposes
while i < cap:
    #populate volunteers
    try:
        r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i)) #load task 
        loaded_r = json.loads(r.text) 

        if len(loaded_r) != 6: #if task exists
            user = loaded_r['user_id']
            timestamp = loaded_r['finish_time']

            link = loaded_r['links'][1]
            #assuming well-formatted data, we can slice the parent link and get article data
            parent_link = link.split(" ")[3][6:-3]  
            p = requests.get(parent_link.format(i)) #load task 
            loaded_p = json.loads(p.text)

            article_id = loaded_p['info']['article']['id'] #can't find article_sha256!!
            article_name = loaded_p['info']['article']['metadata']['filename']
            
            #if 'topic_name' in loaded_r['info']['highlight_group'].keys(): #key errors
            #    topic = loaded_r['info']['highlight_group']['topic_name']

            date = timestamp[0:10]
            
            data = {'date':date, 'article_id':article_id, 'article_name':article_name}
            #data = {'date':date, 'article_sha256':article_sha256, 'article_name':article_name, 'topic':topic} #from bryant
            if user in volunteers:
                volunteers[user].append(data)
            else:
                volunteers[user] = [data]
    except:
        pass
    print(i)
    i += 1
    r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))
    while r.status_code == 404 and i < cap:
            #if the request is an error, let's skip it
            #update_curr_cell(i) #from bryant
            print('skipping', i)
            i += 1
            r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))
    while r.status_code == 429 and i < cap:
            #if we're sending too many requests, let's sleep and try again
            print('waiting...')
            time.sleep(30)
            r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('pe-volunteer')

for user_id, contribution_info in volunteers.items():
    contribution_info = json.dumps(contribution_info)
    response = table.put_item(
        Item={
            'user_id': str(user_id),
            'contribution_info': contribution_info,
        }
    )

