# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import re
import os
import sys
from pprint import pprint
from collections import OrderedDict

# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui
from .ui.dialog import Ui_Form


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """
    # in order to handle UIs seamlessly, each toolkit engine has methods for launching
    # different types of windows. By using these methods, your windows will be correctly
    # decorated and handled in a consistent fashion by the system.

    # we pass the dialog class to this method and leave the actual construction
    # to be carried out by toolkit.
    app_instance.engine.show_dialog("Shotgun Schema Introspection", app_instance, SGSchemaIntrospectionUi)


class SGSchemaIntrospectionUi(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # most of the useful accessors are available through the Application class instance
        # it is often handy to keep a reference to this. You can get it via the following method:
        self._app = sgtk.platform.current_bundle()

        # via the self._app handle we can for example access:
        # - The engine, via self._app.engine
        # - A Shotgun API instance, via self._app.shotgun
        # - A tk API instance, via self._app.tk

        self.sg = self._app.shotgun

        self.entities = None
        self.eSort = []
        self.eDisp = {}
        self.curEIndx = -1
        self.curType = None
        self.curData = None

        self.fSort = []
        self.fdList = {}

        self.ui.entityTable.itemClicked.connect(self.chooseEntity)
        self.ui.fieldsTable.itemClicked.connect(self.getFieldData)
        self.ui.refreshPushButton.released.connect(self.getEntities)

        self.getEntities()

    def getEntities(self):
        remove_connections = self.ui.removeConnectionsCheckBox.isChecked()

        self.entities = self.sg.schema_entity_read()

        # Remove Connections from list
        new_dict = {}
        for key, value in self.entities.items():
            if remove_connections:
                if re.search('Connection', key):
                    continue
            new_dict[key] = value

        self.entities = OrderedDict(sorted(new_dict.items(), key=lambda t: t[1]['name']['value']))

        i = 0
        self.ui.entityTable.clearContents()
        self.ui.entityTable.setRowCount(len(self.entities))
        for entity_type, entity_name in self.entities.items():
            item = QtGui.QTableWidgetItem(entity_name['name']['value'])
            self.ui.entityTable.setItem(i, 0, item)
            item = QtGui.QTableWidgetItem(entity_type)
            self.ui.entityTable.setItem(i, 1, item)
            i += 1

        self.ui.entityTable.resizeColumnsToContents()

    def chooseEntity(self, item):
        entity_type = None
        item = self.ui.entityTable.item(item.row(), 1)
        if item:
            entity_type = item.text()

        if not entity_type:
            return

        self.curData = self.sg.schema_field_read(entity_type)

        # Sort and List Fields
        self.fSort = list(self.curData.keys())
        self.fSort.sort()
        self.fdList = {}
        for each in self.fSort:
            self.fdList[each] = {}
            self.fdList[each]['dname'] = self.curData[each]['name']['value']
            self.fdList[each]['kname'] = each
            j_list = []
            j_sort = list(self.curData[each].keys())
            j_sort.sort()
            for j in j_sort:
                j_list.append(j)
                j_list.append('\t%s' % str(self.curData[each][j]))
            self.fdList[each]['data'] = '\n'.join(j_list)

        self.ui.fieldsTable.clearContents()
        self.ui.fieldsTable.setRowCount(len(self.fdList))
        for i, each in enumerate(self.fSort):
            item = QtGui.QTableWidgetItem(self.fdList[each]['dname'])
            self.ui.fieldsTable.setItem(i, 0, item)
            item = QtGui.QTableWidgetItem(self.fdList[each]['kname'])
            self.ui.fieldsTable.setItem(i, 1, item)

        self.ui.fieldsTable.horizontalHeader().setStretchLastSection(True)
        self.ui.fieldsTable.resizeColumnsToContents()

    def getFieldData(self, item):
        self.cur_field = self.fSort[item.row()]
        self.ui.FieldDataEdt.clear()
        self.ui.FieldDataEdt.setPlainText(self.fdList[self.cur_field]['data'])
