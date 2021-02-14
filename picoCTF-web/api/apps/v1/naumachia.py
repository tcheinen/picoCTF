"""
Docker related endpoints.

XXX.
"""

from flask import jsonify, send_file
from flask_restplus import Namespace, Resource

import api
from api import docker
from api import block_before_competition, PicoException, require_admin, require_login

import string

from io import BytesIO
from urllib.request import urlopen
from urllib.error import HTTPError
import json
import logging

logger = logging.getLogger(__name__)

host = "localhost:3960"
registrar_timeout = 10

ns = Namespace("docker", description="On-Demand (docker) instance management")

def send_config(host, challengeID, username):
    url = "http://{0}/{1}/get?cn={2}".format(host, challengeID, username)
    logger.debug("Requesting: {0}".format(url))
    resp = urlopen(url, timeout=registrar_timeout)
    config = json.loads(resp.read().decode('utf-8')).encode('utf-8')
    return send_file(
        BytesIO(config),
        attachment_filename="{0}.ovpn".format(challengeID),
        as_attachment=True
    )

@block_before_competition
@require_login
@ns.response(200, "Success")
@ns.response(401, "Not logged in")
@ns.response(403, "Not authorized")
@ns.response(404, "Instance not found")
@ns.route("/<string:challengeID>")
class NaumachiaChallenge(Resource):

    def get(self, challengeID):
        user_account = api.user.get_user()
        username = user_account['username']
        try:
            resp = send_config(host, challengeID, username)
            logger.info("[200] Client {0} requested config for challenge {1}".format(username, challengeID))
            return resp
        except HTTPError as err:
            if err.code != 404:
                logger.info("[500] Config retrival failed for challenge {0}".format(challengeID))
                raise

        try:
            url = "http://{0}/{1}/add?cn={2}".format(host, challengeID, username)
            logger.debug("Requesting: {0}".format(url))
            urlopen(url, timeout=registrar_timeout)

            resp = send_config(host, challengeID, username)
            logger.info("[200] Client {0} requested new config for challenge {1}".format(username, challengeID))
            return resp
        except HTTPError:
            logger.info("[500] Config creation failed for challenge {0}".format(challengeID))
            raise
