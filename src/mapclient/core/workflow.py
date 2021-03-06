'''
MAP Client, a program to generate detailed musculoskeletal models for OpenSim.
    Copyright (C) 2012  University of Auckland

This file is part of MAP Client. (http://launchpad.net/mapclient)

    MAP Client is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    MAP Client is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MAP Client.  If not, see <http://www.gnu.org/licenses/>..
'''
import os
import shutil
import logging

from PySide import QtCore

from mapclient.settings import info
from mapclient.core.workflowscene import WorkflowScene
from mapclient.core.workflowerror import WorkflowError
from mapclient.core.workflowrdf import serializeWorkflowAnnotation
from mapclient.settings.general import getConfigurationFile, getVirtEnvDirectory, \
    DISPLAY_FULL_PATH, getConfiguration
from mapclient.tools.virtualenv.manager import VirtualEnvManager
import pkgutil
from mapclient.core.pluginframework import PluginDatabase

logger = logging.getLogger(__name__)

_PREVIOUS_LOCATION_STRING = 'previousLocation'

def _getWorkflowConfiguration(location):
#     print('get workflow confiburation: ' + location)
    return QtCore.QSettings(_getWorkflowConfigurationAbsoluteFilename(location), QtCore.QSettings.IniFormat)

def _getWorkflowConfigurationAbsoluteFilename(location):
#     print('get workflow configuration abs filename: ' + os.path.join(location, info.DEFAULT_WORKFLOW_PROJECT_FILENAME))
    return os.path.join(location, info.DEFAULT_WORKFLOW_PROJECT_FILENAME)

def _getWorkflowMetaAbsoluteFilename(location):
    return os.path.join(location, info.DEFAULT_WORKFLOW_ANNOTATION_FILENAME)

class WorkflowManager(object):
    '''
    This class manages (models?) the workflow.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.name = 'WorkflowManager'
#        self.widget = None
#        self.widgetIndex = -1
        self._location = ''
        self._conf_filename = None
        self._previousLocation = None
        self._saveStateIndex = 0
        self._currentStateIndex = 0

        self._title = None

        self._plugin_database = None
        self._scene = WorkflowScene(self)

    def title(self):
        self._title = info.APPLICATION_NAME
        if self._location:
            if getConfiguration(DISPLAY_FULL_PATH):
                self._title = self._title + ' - ' + self._location
            else:
                self._title = self._title + ' - ' + os.path.basename(self._location)
        if self._saveStateIndex != self._currentStateIndex:
            self._title = self._title + ' *'

        return self._title

    # Why set/get? all _prefix are public anyway, just use attributes...
    # if they need to be modified they can be turned into properties
    def setLocation(self, location):
        self._location = location

    def location(self):
        return self._location

    def setPreviousLocation(self, location):
        self._previousLocation = location

    def previousLocation(self):
        return self._previousLocation

    def setPluginDatabase(self, plugin_database):
        self._plugin_database = plugin_database

    def scene(self):
        return self._scene

    def undoStackIndexChanged(self, index):
        self._currentStateIndex = index

    def identifierOccursCount(self, identifier):
        return self._scene.identifierOccursCount(identifier)

    def execute(self):
        self._scene.execute()

    def isModified(self):
        return self._saveStateIndex != self._currentStateIndex

    def changeIdentifier(self, old_identifier, new_identifier):
        old_config = getConfigurationFile(self._location, old_identifier)
        new_config = getConfigurationFile(self._location, new_identifier)
        shutil.move(old_config, new_config)

    def new(self, location):
        '''
        Create a new workflow at the given location.  The location is a directory, it must exist
        it will not be created.  A file '.workflow.conf' is created in the directory at 'location' which holds
        information relating to the workflow.
        '''
        if location is None:
            raise WorkflowError('No location given to create new Workflow.')

        if not os.path.exists(location):
            raise WorkflowError('Location %s does not exist.' % location)

        self._location = location
        wf = _getWorkflowConfiguration(location)
        wf.setValue('version', info.VERSION_STRING)
#        self._title = info.APPLICATION_NAME + ' - ' + location
        self._scene.clear()

    def exists(self, location):
        '''
        Determines whether a workflow exists in the given location.
        Returns True if a valid workflow exists, False otherwise.
        '''
        if location is None:
            return False

        if not os.path.exists(location):
            return False

        wf = _getWorkflowConfiguration(location)
        if wf.contains('version'):
            return True

        return False

    def load(self, location):
        '''
        Open a workflow from the given location.
        :param location:
        '''
        if location is None:
            raise WorkflowError('No location given to open Workflow.')

        if not os.path.exists(location):
            raise WorkflowError('Location %s does not exist' % location)

        wf = _getWorkflowConfiguration(location)
        if not wf.contains('version'):
            raise WorkflowError('The given Workflow configuration file is not valid.')

        workflow_version = versionTuple(wf.value('version'))
        application_version = versionTuple(info.VERSION_STRING)
        if not compatibleVersions(workflow_version, application_version):
            pass  # should already have thrown an exception

        self._location = location
        self._scene.loadState(wf)
        self._saveStateIndex = self._currentStateIndex = 0

    def save(self):
        wf = _getWorkflowConfiguration(self._location)
        if 'version' not in wf.allKeys():
            wf.setValue('version', info.VERSION_STRING)
        self._scene.saveState(wf)
        self._plugin_database.saveState(wf, self._scene)
        self._saveStateIndex = self._currentStateIndex
        af = _getWorkflowMetaAbsoluteFilename(self._location)
        f = open(af, 'w')
        f.write(serializeWorkflowAnnotation().decode('utf-8'))
        self._scene.saveAnnotation(f)
        f.close()

#        self._title = info.APPLICATION_NAME + ' - ' + self._location

    def close(self):
        '''
        Close the current workflow
        '''
        self._location = ''
        self._saveStateIndex = self._currentStateIndex = 0
#        self._title = info.APPLICATION_NAME

    def isWorkflowOpen(self):
        return True  # not self._location == None

    def isWorkflowTracked(self):
        markers = ['.git', '.hg']
        for marker in markers:
            target = os.path.join(self._location, marker)
            logger.debug('checking isdir: %s', target)
            return os.path.isdir(target)
        return False

    def _loadWorkflowPlugins(self, wf_location):
        wf = _getWorkflowConfiguration(wf_location)

        return PluginDatabase.load(wf)

    def checkPlugins(self, wf_location):
        required_plugins = self._loadWorkflowPlugins(wf_location)
        missing_plugins = self._plugin_database.checkForMissingPlugins(required_plugins)
        return missing_plugins

    def checkDependencies(self, wf_location):
        required_plugins = self._loadWorkflowPlugins(wf_location)
        virtenv_dir = getVirtEnvDirectory()
        vem = VirtualEnvManager(virtenv_dir)
        missing_dependencies = {}
        if vem.exists():
            missing_dependencies = self._plugin_database.checkForMissingDependencies(required_plugins, vem.list())
        return missing_dependencies

    def writeSettings(self, settings):
        settings.beginGroup(self.name)
        settings.setValue(_PREVIOUS_LOCATION_STRING, self._previousLocation)
        settings.endGroup()

    def readSettings(self, settings):
        settings.beginGroup(self.name)
        self._previousLocation = settings.value(_PREVIOUS_LOCATION_STRING, '')
        settings.endGroup()


def versionTuple(v):
    return tuple(map(int, (v.split("."))))


def compatibleVersions(workflow_version, application_version):
    """
    Method checks whether two versions are compatible or not.  Raises a
    WorkflowError exception if the two versions are not compatible.
    True if they are and False otherwise.
    The inputs are expected to be tuples of the version number:
    (major, minor, patch)
    """

    # Start with database of known compatible versions then check for
    # standard problems.
    if application_version == (0, 12, 0) and workflow_version == (0, 11, 3):
        return True

    if not workflow_version[0:2] == application_version[0:2]:
        # compare first two elements of version (major, minor)
        raise WorkflowError(
            'Major/Minor version number mismatch - '
            'workflow version: %s; application version: %s.' %
                (workflow_version, application_version)
        )
    if not application_version[2] <= workflow_version[2]:
        raise WorkflowError(
            'Patch version number of the workflow cannot be newer than '
            'application - '
            'workflow version: %s; application version: %s.' %
                (workflow_version, application_version)
        )

    return True


