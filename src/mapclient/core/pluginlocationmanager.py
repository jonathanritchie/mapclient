# '''
# MAP Client, a program to generate detailed musculoskeletal models for OpenSim.
#     Copyright (C) 2012  University of Auckland
#     
# This file is part of MAP Client. (http://launchpad.net/mapclient)
# 
#     MAP Client is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     MAP Client is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with MAP Client.  If not, see <http://www.gnu.org/licenses/>..
# '''
# 
# class PluginLocationManager:
#     '''
#     Manages plugin information for the current workflow.
#     '''
# 
#     def __init__(self):
#         self._database = {}
# 
#     def saveState(self, ws, scene):
#         '''
#         Save the state of the current workflow plugin requirements 
#         to the given workflow configuration.
#         '''
#         ws.remove('required_plugins')
#         ws.beginGroup('required_plugins')
#         ws.beginWriteArray('plugin')
#         pluginIndex = 0
#         for item in scene._items:
#             if item.Type == 'Step':
#                 step_name = item._step.getName()
#                 if step_name in self._database:
#                     information_dict = self._database[step_name]
#                     ws.setArrayIndex(pluginIndex)
#                     ws.setValue('name', step_name)
#                     ws.setValue('author', information_dict['author'])
#                     ws.setValue('version', information_dict['version'])
#                     ws.setValue('location', information_dict['location'])
# 
#                     ws.beginWriteArray('dependencies')
#                     for dependency_index, dependency in enumerate(information_dict['dependencies']):
#                         ws.setArrayIndex(dependency_index)
#                         ws.setValue('dependency', dependency)
#                     ws.endArray()
#                     ws.setValue('dependencies', information_dict['dependencies'])
# 
#                     pluginIndex += 1
#         ws.endArray()
#         ws.endGroup()
# 
#     @staticmethod
#     def load(ws):
#         '''
#         Load the given Workflow configuration and return it as a dict.
#         '''
#         pluginDict = {}
#         ws.beginGroup('required_plugins')
#         pluginCount = ws.beginReadArray('plugin')
#         for i in range(pluginCount):
#             ws.setArrayIndex(i)
#             name = ws.value('name')
#             pluginDict[name] = {
#                 'author':ws.value('author'),
#                 'version':ws.value('version'),
#                 'location':ws.value('location')
#             }
#             dependencies = []
#             dependency_count = ws.beginReadArray('dependencies')
#             for j in range(dependency_count):
#                 ws.setArrayIndex(j)
#                 dependencies.append(ws.value('dependency'))
#             ws.endArray()
#             pluginDict[name]['dependencies'] = dependencies
#         ws.endArray()
#         ws.endGroup()
#         
#         return pluginDict
# 
#     def addLoadedPluginInformation(self, plugin_name, step_name, plugin_author, plugin_version, plugin_location, plugin_dependencies):
#         plugin_dict = {}
#         plugin_dict['plugin name'] = plugin_name
#         plugin_dict['author'] = plugin_author
#         plugin_dict['version'] = plugin_version
#         plugin_dict['location'] = plugin_location
#         plugin_dict['dependencies'] = plugin_dependencies
#         self._database[step_name] = plugin_dict
#         print 'add loaded plugin information'
# 
#     def checkForMissingPlugins(self, to_check):
#         '''
#         Check for the given plugin dict against the dict of plugins currently available. 
#         '''
#         print 'have'
#         print self._database
#         missing_plugins = {}
#         for plugin in to_check:
#             if not (plugin in self._database and \
#                 to_check[plugin]['author'] == self._database[plugin]['author'] and \
#                 to_check[plugin]['version'] == self._database[plugin]['version']):
#                 missing_plugins[plugin] = to_check[plugin]
# 
#         return missing_plugins
# 
#     def getPluginDatabase(self):
#         return self._database
