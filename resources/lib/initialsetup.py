# -*- coding: utf-8 -*-

#################################################################################################

import logging

import xbmc
import xbmcgui

import clientinfo
import connectmanager
import connect.connectionmanager as connectionmanager
import userclient
from utils import settings, language as lang, passwordsXML

#################################################################################################

log = logging.getLogger("EMBY."+__name__)
STATE = connectionmanager.ConnectionState

#################################################################################################


class InitialSetup(object):


    def __init__(self):

        self.addon_id = clientinfo.ClientInfo().get_addon_id()
        self.user_client = userclient.UserClient()
        self.connectmanager = connectmanager.ConnectManager()


    def setup(self):
        # Check server, user, direct paths, music, direct stream if not direct path.
        dialog = xbmcgui.Dialog()

        log.debug("Initial setup called")

        if self._server_verification() and settings('userId'):
            # Setup is already completed
            return

        if not self._user_identification():
            # User failed to identify
            return

    def _server_verification(self):

        ###$ Begin migration $###
        if settings('server') == "":
            self.user_client.get_server()
            log.info("server migration completed")

        self.user_client.get_userid()
        self.user_client.get_token()
        ###$ End migration $###

        current_server = self.user_client.get_server()
        if current_server and not settings('serverId'):
            server = self.connectmanager.get_server(current_server,
                                                        {'ssl': self.user_client.get_ssl()})
            log.info("Detected: %s", server)
            try:
                server_id = server['Servers'][0]['Id']
                settings('serverId', value=server_id)
            except Exception as error:
                log.error(error)

        if current_server:
            current_state = self.connectmanager.get_state()
            try:
                for server in current_state['Servers']:
                    if server['Id'] == settings('serverId'):
                        # Update token
                        server['UserId'] = settings('userId') or None
                        server['AccessToken'] = settings('token') or None
                        self.connectmanager.update_token(server)

                        server_address = self.connectmanager.get_address(server)
                        self._set_server(server_address, server)
                        log.info("Found server!")
            except Exception as error:
                log.error(error)
            
            return True

        return False

    def _user_identification(self):

        try:
            server = self.connectmanager.select_servers()
            log.info("Server: %s", server)
            server_address = self.connectmanager.get_address(server)
            self._set_server(server_address, server)

            if not server.get('AccessToken') and not server.get('UserId'):
                user = self.connectmanager.login(server)
                log.info("User authenticated: %s", user)
                settings('username', value=user['User']['Name'])
                self._set_user(user['User']['Id'], user['AccessToken'])
            else: # Logged with Emby Connect
                user = self.connectmanager.get_state()
                settings('connectUsername', value=user['ConnectUser']['Name'])
                self._set_user(server['UserId'], server['AccessToken'])

            return True

        except RuntimeError as error:
            log.exception(error)
            xbmc.executebuiltin('Addon.OpenSettings(%s)' % self.addon_id)
            return False

    @classmethod
    def _set_server(cls, server_address, server):

        settings('serverName', value=server['Name'])
        settings('serverId', value=server['Id'])
        settings('server', value=server_address)

    @classmethod
    def _set_user(cls, user_id, token):

        settings('userId', value=user_id)
        settings('token', value=token)
