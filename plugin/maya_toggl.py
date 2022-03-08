"""
Script: maya_toggl
Version: 0.1
Author: Johannes Andersson
Contact: hello@thejoltjoker.com
Description: Initiates the toggl menu
"""
import logging
from maya import cmds
from imp import reload

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def initializePlugin(obj):
    from maya_toggl import menu as mt_menu
    reload(mt_menu)
    mt_menu.Menu()
    logger.info('Toggl menu loaded')


def uninitializePlugin(obj):
    cmds.deleteUI('maya_toggl')

    logger.info('Toggl menu unloaded')
