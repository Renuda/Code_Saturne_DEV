# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------

# This file is part of Code_Saturne, a general-purpose CFD tool.
#
# Copyright (C) 1998-2020 EDF S.A.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA 02110-1301, USA.

# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# Standard modules
# -------------------------------------------------------------------------------

import logging

# -------------------------------------------------------------------------------
# Third-party modules
# -------------------------------------------------------------------------------

from code_saturne.Base.QtCore import *
from code_saturne.Base.QtGui import *
from code_saturne.Base.QtWidgets import *

# -------------------------------------------------------------------------------
# Application modules import
# -------------------------------------------------------------------------------

from code_saturne.model.Common import GuiParam
from code_saturne.model.LocalizationModel import LocalizationModel, Zone

from code_saturne.Pages.VolumicTermsForm import Ui_VolumicTermsForm

# -------------------------------------------------------------------------------
# Widgets import
# -------------------------------------------------------------------------------

# -------------------------------------------------------------------------------
# log config
# -------------------------------------------------------------------------------

logging.basicConfig()
log = logging.getLogger("VolumicTermsView")
log.setLevel(GuiParam.DEBUG)


class VolumicZoneNatureModel(QAbstractTableModel):

    def __init__(self, zoneModel, parent=None):
        super(VolumicZoneNatureModel, self).__init__(parent)
        self._zoneModel = zoneModel
        self._headers = []
        self._data = []
        self._model2View = {}
        self._view2Model = {}
        self.defineHeaders()
        self.extractDataFromModel()

    def defineHeaders(self):
        zones = self._zoneModel.getZones()
        if zones:
            self._model2View = zones[0].getModel2ViewDictionary()
            self._view2Model = {value: key for key, value in self._model2View.items()}
            self._headers = ["Zone label"]
            for nature in zones[0].getNatureList():
                self._headers.append(self._model2View[nature])
            self._headers.sort(key=sort_headers)

    def extractDataFromModel(self):
        for zone in self._zoneModel.getZones():
            data = [zone.getLabel()]
            for nature in self._headers[1:]:
                if nature in self._view2Model.keys():
                    data.append(zone.isNatureActivated(self._view2Model[nature]))
                else:
                    data.append(False)
            self._data.append(data)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole and index.column() == 0:
            return QVariant(self._data[index.row()][index.column()])
        elif role == Qt.CheckStateRole and index.column() > 0:
            return self.checkState(QPersistentModelIndex(index))
        else:
            return QVariant()

    def checkState(self, index):
        if not index.isValid():
            return Qt.Unchecked
        return bool2CheckState(self._data[index.row()][index.column()])

    def setData(self, index, value, role=Qt.DisplayRole):
        if not index.isValid():
            return False
        if index.column() > 0:
            value = checkState2Bool(value)
        self._data[index.row()][index.column()] = value
        self.setModelFromData()
        self.dataChanged.emit(index, index)
        return True

    def setModelFromData(self):
        # TODO : move the creation of a new zone to LocalizationModel.replaceZone, but need to check impact on LocalizationView first.
        for row in self._data:
            old_label = row[0]
            old_zone = self._zoneModel.selectZone(old_label)
            print(old_zone)
            new_nature = {}
            for i, header in enumerate(self._headers[1:]):
                nature = self._view2Model[header]
                if row[i + 1]:
                    new_nature[nature] = "on"
                else:
                    new_nature[nature] = "off"
            new_zone = Zone("VolumicZone",
                            case=old_zone.case,
                            label=row[0],
                            codeNumber=old_zone.getCodeNumber(),
                            localization=old_zone.getLocalization(),
                            nature=new_nature)
            self._zoneModel.replaceZone(old_zone, new_zone)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self._headers[section])
        return None

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._headers)

    def flags(self, index):
        base_flags = Qt.ItemIsEnabled
        if index.column() == 0:
            return base_flags
        else:
            return base_flags | Qt.ItemIsUserCheckable


# Helper functions

def sort_headers(header):
    ordered_headers = ["Zone label",
                       "Initialization",
                       "Porosity",
                       "Head losses",
                       "Momentum source\n term",
                       "Volumic source\n term",
                       "Thermal source term",
                       "Scalar source term",
                       "Groundwater\n volumic law"]
    return ordered_headers.index(header)


def checkState2Bool(check_state):
    return {Qt.Unchecked: False, Qt.Checked: True}[check_state]


def bool2CheckState(bool_value):
    return {True: Qt.Checked, False: Qt.Unchecked}[bool_value]


# -------------------------------------------------------------------------------
# Main class
# -------------------------------------------------------------------------------

class VolumicTermsView(QWidget, Ui_VolumicTermsForm):
    """ Display available volumic treatments for a given zone """

    def __init__(self, parent, case):
        QWidget.__init__(self, parent)
        Ui_VolumicTermsForm.__init__(self)
        self.setupUi(self)

        self.case = case
        self.parent = parent

        # Get list of zones
        self.zoneModel = LocalizationModel("VolumicZone", self.case)
        self.tableModel = VolumicZoneNatureModel(self.zoneModel)
        self.volumicZoneNatureTableView.setModel(self.tableModel)
        self.case.undoStopGlobal()
