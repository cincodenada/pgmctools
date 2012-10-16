#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
from webapp2_extras import mako, sessions
import pickle
import httplib2
import gdata.docs.service
import gdata.spreadsheets.client
import gdata.gauth
import os
import urllib
import re
from datetime import datetime
import json
from operator import itemgetter

from ConfigParser import SafeConfigParser
import argparse

SPREADSHEET_SCOPE='https://spreadsheets.google.com/feeds/'

parser = argparse.ArgumentParser()
parser.add_argument('config',type=str,help='A config file to read from.',default='config.ini');
args = parser.parse_args()

extconf = SafeConfigParser()
extconf.read('defaults.ini');
extconf.read(args.config)

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': extconf.get('auth','session_key'),
}

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            token_data = self.session['token_data']
            self.token = gdata.gauth.OAuth2Token(
                client_id=extconf.get('auth','client_id'),
                client_secret=extconf.get('auth','client_secret'),
                scope=SPREADSHEET_SCOPE,
                user_agent='cincodenada',
                access_token=token_data['access_token']
            )
        except (KeyError, gdata.client.RequestError):
            try:
                del self.session['token_data']
            except:
                pass

            self.token = gdata.gauth.OAuth2Token(
                client_id=extconf.get('auth','client_id'),
                client_secret=extconf.get('auth','client_secret'),
                scope=SPREADSHEET_SCOPE,
                user_agent='cincodenada'
            )
            self.token.redirect_uri = 'http://%s:%d/oauth_callback' % (extconf.get('server','host'),extconf.getint('server','port'))
            code=self.request.get('code')
            print self.request.url
            print code
            if(code):
                print "Return URL (code):" + self.session['return_to']
                self.token.get_access_token(code)
                self.session['token_data'] = {
                    'access_token': self.token.access_token, 
                    'refresh_token': self.token.refresh_token
                }
            else:
                self.session['return_to'] = self.request.path
                print "Return URL:" + self.session['return_to']
                self.session_store.save_sessions(self.response)
                return self.redirect(self.token.generate_authorize_url(redirect_uri=self.token.redirect_uri))

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    @webapp2.cached_property
    def mako(self):
        # Returns a Mako renderer cached in the app registry.
        return mako.get_mako(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.mako.render_template(_template, **context)
        self.response.write(rv)

class OAuthHandler(BaseHandler):
    def get(self):
        try:
            nexturl = self.session['return_to']
        except:
            nexturl='/'

        self.redirect(nexturl)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

class AttendanceUpdateHandler(BaseHandler):
    def post(self, params=None):
        updater = gdata.spreadsheets.data.build_batch_cells_update(ATTENDANCE_KEY, self.request.post('wkey'))
        self.token.authorize(updater)
        updater.add_set_cell(self.request.post('row'),self.request.post('col'),self.request.post('value'))
        for entry in updater.entry:
            print entry

class AttendanceHandler(BaseHandler):
    def get(self, params=None):
        
        spr_client = gdata.spreadsheets.client.SpreadsheetsClient()
        self.token.authorize(spr_client)
        try:
            allsheets = spr_client.get_worksheets(extconf.get('spreadsheet','key')).entry
        except gdata.client.RequestError:
            del self.session['token_data']
            return self.redirect(self.request.url)
        worksheetlist = {}
        for entry in allsheets:
            if(entry.title.text.find('Attendance') > -1):
                print entry.id.text
                mo = re.search("\/([\w\d]+)$",entry.id.text)
                print mo.group(1)
                if(not mo is None):
                    worksheetlist[mo.group(1)] = entry.title.text

        cursheet = self.request.get('wkey')
        curdate = self.request.get('date')
        datelist = {}
        attdata = {}
        namedata = {}
        namelist = []
        namecols = ['last','first','status_holiday','status_spring','status_summer']
        if(cursheet):
            #Load the column headings
            headerQuery = gdata.spreadsheets.client.CellQuery(
                min_row=2,
                max_row=2,
                min_col=6
            )

            sheetlist = spr_client.get_cells(extconf.get('spreadsheet','key'), cursheet, query=headerQuery)
            for entry in sheetlist.entry:
                try:
                    date = datetime.strptime(entry.cell.text, '%m/%d')
                    datelist[entry.cell.col] = entry.cell.text
                    print date
                    print entry.cell.col + ":" + entry.cell.text
                except ValueError:
                    pass
            
            if(curdate):
                nameQuery = gdata.spreadsheets.client.CellQuery(
                    min_row=3,
                    min_col=1,
                    max_col=5
                )
                attQuery = gdata.spreadsheets.client.CellQuery(
                    min_row=3,
                    min_col=curdate,
                    max_col=curdate
                )

                namefeed = spr_client.get_cells(extconf.get('spreadsheet','key'), cursheet, query=nameQuery)
                for cell in namefeed.entry:
                    if(not cell.cell.row in namedata):
                        namedata[cell.cell.row] = {'row':cell.cell.row}

                    namedata[cell.cell.row][namecols[int(cell.cell.col) - 1]] = cell.cell.text

                attlist = spr_client.get_cells(extconf.get('spreadsheet','key'), cursheet, query=attQuery)
                for cell in attlist.entry:
                    attdata[cell.cell.row] = cell.cell.text

                #Sort names by last, first
                namelist = namedata.values();
                namelist.sort(key=itemgetter('first'))
                namelist.sort(key=itemgetter('last'))

                print attdata
                print namedata

        context = {'cursheet':cursheet,'curdate':curdate,'worksheets': worksheetlist, 'dates':datelist, 'attdata': attdata, 'namelist':namelist}
        self.render_response('attendance.html', **context)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/att/update', AttendanceUpdateHandler),
    ('/att/(.*)', AttendanceHandler),
    ('/att', AttendanceHandler),
    ('/oauth_callback', OAuthHandler)
], config=config, debug=True)

def main():
    from paste import httpserver
    httpserver.serve(app, host=extconf.get('server','host'), port=extconf.getint('server','port'))

if __name__ == '__main__':
    main()
