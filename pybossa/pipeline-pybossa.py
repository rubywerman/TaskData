import requests 
import json 
import time
import boto3

volunteers = {}
i = 0
r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))
CACHE_FILENAME = "curr.txt"

def get_curr_cell():
    f = open(CACHE_FILENAME, "r")
    text = f.read()
    f.close()
    return text

def update_curr_cell(new_row):
    f = open(CACHE_FILENAME, "w+")
    f.write(str(new_row))
    f.close()

#i = get_curr_cell()
while i < 50:
    try:
        loaded_r = json.loads(r.text)

        user = loaded_r['user_id']

        timestamp = loaded_r['finish_time']

        article_sha256 = loaded_r['info']['highlight_group']['article_sha256']
        article_name = loaded_r['info']['highlight_group']['article_batch_name']

        if 'topic_name' in loaded_r['info']['highlight_group'].keys():
            topic = loaded_r['info']['highlight_group']['topic_name']
        
        date = timestamp[0:10]

        data = {'date':date, 'article_sha256':article_sha256, 'article_name':article_name, 'topic':topic}
        
        if user in volunteers:
            volunteers[user].append(data)
        else:
            volunteers[user] = [data]
    except:
        pass
    
    i += 1
    print(i)
    r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))
    while r.status_code == 404:
            #print("Stopping at " + i)
            #update_curr_cell(i)
            i += 1
            print(i, 'skipping')
            r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))
            #break
    while r.status_code == 429:
            time.sleep(10)
            r = requests.get('https://pe.goodlylabs.org/api/taskrun/{}'.format(i))
            print('waiting')
            print(i)


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('pe-volunteer')

for user_id, contribution_info in volunteers.items():
    response = table.get_item(
        Key={
            'user_id':user_id
        }
    )
    if 'Item' in response.keys():
        curr_data = json.loads(response['Item']['info'])
        contribution_info = curr_data + contribution_info

    contribution_info = json.dumps(contribution_info)
    response = table.update_item(
        Key={
            'id': user_id
        },
        UpdateExpression="set contribution_info=:c",
        ExpressionAttributeValues={
            ':c': contribution_info,
        },
        ReturnValues="UPDATED_NEW"
    )