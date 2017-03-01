# -*- coding: utf-8 -*-

#################################################################################################

import logging
import os
import sys

import xbmc
import xbmcaddon

#################################################################################################

_ADDON = xbmcaddon.Addon(id='emby.for.kodi')
_CWD = _ADDON.getAddonInfo('path').decode('utf-8')
_BASE_LIB = xbmc.translatePath(os.path.join(_CWD, 'resources', 'lib')).decode('utf-8')
sys.path.append(_BASE_LIB)

#################################################################################################

import loghandler
from service_entry import Service
from utils import settings
from ga_client import GoogleAnalytics

#################################################################################################

loghandler.config()
log = logging.getLogger("EMBY.service")
DELAY = int(settings('startupDelay') or 0)

#################################################################################################

if __name__ == "__main__":

    log.warn("Delaying emby startup by: %s sec...", DELAY)
    service = Service()

    try:
        abort = False
        if DELAY and xbmc.Monitor().waitForAbort(DELAY):
            log.info("Abort event while waiting to start Emby for kodi")
            abort = True
        # Start the service
        if abort == False:
            service.service_entry_point()

    except Exception as error:
        if not (hasattr(error, 'quiet') and error.quiet):
            ga = GoogleAnalytics()
            errStrings = ga.formatException()
            ga.sendEventData("Exception", errStrings[0], errStrings[1])
        log.exception(error)
        log.info("Forcing shutdown")
        service.shutdown()
