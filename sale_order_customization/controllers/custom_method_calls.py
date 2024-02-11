import json
import odoo
import urllib
import base64
import logging
from psycopg2 import IntegrityError, InternalError
import werkzeug

from datetime import datetime, timedelta
from oauthlib.common import add_params_to_uri

from odoo.service import model
from odoo import http, tools, SUPERUSER_ID
from odoo.http import Response, request
from odoo.exceptions import UserError
# from odoo.addons.sale_order_customization.models import sale_order_ext
from odoo.tools.safe_eval import safe_eval
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, date_utils

_logger = logging.getLogger(__name__)


class MyCustomException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.msg = message

    # def __str__(self):
    #     return self.msg


class CustomMethodCalls(http.Controller):
    def get_response(self, status_code, status, data=None):
        """Returns Response Object with given status code and status"""
        response = Response()
        response.status = status
        if data:
            try:
                response.data = isinstance(data, str) and data or json.dumps(data)
                if request.httprequest.headers.get('Accept') == 'application/json':
                    response.mimetype = 'application/json'
            except Exception as e:
                response.data = str(data)
        response.status_code = status_code
        return response

    def _check_credentials(self, kwargs):
        """
            Validates the authentication, If request is using OAuth1.
        """
        kwargs = self._get_credentials(kwargs)
        if not set(self._VALIDATION_FIELDS) < set(list(kwargs)):
            return False, False, self.get_response(401, '401',
                                                   {'error': {'code': '401', 'message': 'Authentication Required'}})
        auth_auth_obj = request.env['auth.auth']
        result, err_msg = auth_auth_obj.authentication(kwargs,
                                                       request.httprequest.method,
                                                       request.httprequest.base_url)
        if not result and err_msg:
            return False, False, self.get_response(401, '401', err_msg)
        key = kwargs['oauth_consumer_key']
        user = auth_auth_obj.get_authorize_user(key)
        if not user:
            return False, False, self.get_response(401, '401',
                                                   {'error': {'code': '401', 'message': 'Authentication Required'}})
        return key, user, False

    def _get_credentials(self, kwargs):
        """
            Parse the credentials from request header and query string
        """
        if request.httprequest.headers.get('Authorization'):
            if 'Bearer' in request.httprequest.headers.get('Authorization'):
                params = {'access_token': request.httprequest.headers.get('Authorization').split(' ')[1]}
            else:
                headers = [header.strip(',') for header in request.httprequest.headers.get('Authorization').split(' ')]
                params = [k_v.split('=') for k_v in headers if len(k_v.split('=')) == 2]
                params = dict([(val[0], eval(val[1])) for val in params])
            kwargs.update(params)
        return kwargs

    def valid_authentication(self, kwargs):
        user, auth = False, False
        credentials = self._get_credentials(kwargs)
        if kwargs.get('oauth_signature'):
            kwargs['for_request_data'] = True
            key, auth, invalid = self._check_credentials(kwargs)
            if invalid:
                return False, False, invalid
            user = auth.user_id
        elif credentials.get('access_token'):
            access_token = request.env['auth.access.token'].sudo().search(
                [('access_token', '=', credentials['access_token'])], limit=1)
            if not access_token or datetime.strptime(
                    access_token.access_token_validity.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    DEFAULT_SERVER_DATETIME_FORMAT) < datetime.strptime(
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), DEFAULT_SERVER_DATETIME_FORMAT):
                return False, False, self.get_response(401, str(401), {'code': 401, 'message': 'Access Token Invalid'})
            user, auth = access_token.auth_id.user_id, access_token.auth_id
        elif not request.httprequest.headers.get('Authorization'):
            redirect_url = add_params_to_uri(request.httprequest.base_url, kwargs)
            return False, False, werkzeug.utils.redirect(add_params_to_uri('web/login', {'redirect': redirect_url}))
        return auth, user, False

    @http.route(['/restapi/1.0/object/common/<string:object>/<string:method>'], \
                type="http", auth="public", csrf=False)
    def perform_model_request(self, object, method, *args, **kwargs):
        auth, user, invalid = self.valid_authentication(kwargs)
        payload = request.httprequest.data.decode('utf-8')
        if not user or invalid:
            return self.get_response(401, '401', json.dumps({'code': 401, 'message': 'Authentication required'}))
        try:
            kwargs['vals'] = payload
            result = model.execute_kw(request.cr.dbname, user.id, object, method, args=args, kw=kwargs)
            return json.dumps(result)
        except Exception as e:
            error_message = str(e.msg)
            return self.get_response(400, '400', json.dumps({'code': 400, 'message': error_message}))

