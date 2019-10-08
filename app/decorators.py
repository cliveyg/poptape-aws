# app/decorators.py
#from app.services import call_requests
import requests
from functools import wraps
import os
from dotenv import load_dotenv
from flask import jsonify
from flask import current_app as appy

load_dotenv()

# -----------------------------------------------------------------------------
# these are separate from the views so we can mock them more easily  in tests
# -----------------------------------------------------------------------------

def microservice_only(request):
    def actual_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):    
         
            ip_address = requests.headers.get("X-Real-IP")

            if not ip_address:
                return jsonify({ 'message': 'Hmmm, bit suspicious. Away yer go'}), 401

            if ip_address in good_neighbourhood:
                return f(pub_id, request, *args, **kwargs)

            return jsonify({ 'message': 'Yer name\'s not down. Yer not coming in'}), 401

        return decorated
    return actual_decorator

# -----------------------------------------------------------------------------

def require_access_level(access_level,request): # pragma: no cover
    def actual_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            token = request.headers.get('x-access-token')

            if not token:
                return jsonify({ 'message': 'Naughty one!'}), 401

            headers = { 'Content-Type': 'application/json', 'x-access-token': token }
            url = os.getenv('CHECK_ACCESS_URL')+str(access_level)
            try:
                r = requests.get(url, headers=headers)
            except Exception as err:
                appy.logger.error(str(err))

            if r.status_code != 200:
                return jsonify({ 'message': 'Ooh you are naughty!'}), 401

            returned_json = r.json()

            if 'public_id' in returned_json:
                pub_id = returned_json['public_id']
                return f(pub_id, request, *args, **kwargs)

            return jsonify({ 'message': 'No public_id returned'}), 401

        return decorated
    return actual_decorator 
