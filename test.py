import os
from dotenv import load_dotenv
import json

load_dotenv('.env')


print(json.loads(os.environ.get('CONSULTATIONS')).keys())
