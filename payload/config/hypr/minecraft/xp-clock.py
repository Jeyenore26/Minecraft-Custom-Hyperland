#!/usr/bin/python3
import json
from datetime import datetime

def status(now):
    minute=now.minute
    return {'text':now.strftime('%H:%M'),'class':f'xp-{minute}',
            'tooltip':now.strftime('%A, %d %B %Y')+f'\nHour progress: {minute}/60 minutes',
            'percentage':int(minute/60*100)}
if __name__=='__main__':print(json.dumps(status(datetime.now())))
