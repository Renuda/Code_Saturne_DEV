# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------

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

#-------------------------------------------------------------------------------

"""
This module contains the following classes and function:
- NameDelegate
- ChemicalFormulaDelegate
- ValueDelegate
- StandardItemModelSpecies
- GasCombustionView
"""

#-------------------------------------------------------------------------------
# Library modules import
#-------------------------------------------------------------------------------

import logging, os

#-------------------------------------------------------------------------------
# Third-party modules
#-------------------------------------------------------------------------------

from code_saturne.Base.QtCore    import *
from code_saturne.Base.QtGui     import *
from code_saturne.Base.QtWidgets import *

#-------------------------------------------------------------------------------
# Application modules import
#-------------------------------------------------------------------------------

from code_saturne.model.Common import LABEL_LENGTH_MAX, GuiParam
from code_saturne.Base.QtPage import ComboModel, RegExpValidator
from code_saturne.Base.QtPage import DoubleValidator, from_qvariant
from code_saturne.Base.QtPage import to_text_string
from code_saturne.Base.QtPage import IntValidator
from code_saturne.Pages.GasCombustionForm import Ui_GasCombustionForm
from code_saturne.model.GasCombustionModel import GasCombustionModel
from code_saturne.model.GasCombustionModel import ThermochemistryData

#-------------------------------------------------------------------------------
# log config
#-------------------------------------------------------------------------------

logging.basicConfig()
log = logging.getLogger("GasCombustionView")
log.setLevel(GuiParam.DEBUG)

#-------------------------------------------------------------------------------
# Line edit delegate for the specie label
#-------------------------------------------------------------------------------

class NameDelegate(QItemDelegate):
    """
    Use of a QLineEdit in the table.
    """
    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)
        self.parent = parent
        self.old_pname = ""


    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        self.old_pname = ""
        rx = "[_a-zA-Z][_A-Za-z0-9]{1," + str(LABEL_LENGTH_MAX-1) + "}"
        self.regExp = QRegExp(rx)
        v = RegExpValidator(editor, self.regExp)
        editor.setValidator(v)
        return editor


    def setEditorData(self, editor, index):
        editor.setAutoFillBackground(True)
        value = from_qvariant(index.model().data(index, Qt.DisplayRole), to_text_string)
        self.old_pname = str(value)
        editor.setText(value)


    def setModelData(self, editor, model, index):
        if not editor.isModified():
            return

        if editor.validator().state == QValidator.Acceptable:
            new_pname = str(editor.text())

            if new_pname in model.mdl.getSpecieNamesList():
                default = {}
                default['name']  = self.old_pname
                default['list']   = model.mdl.getSpecieNamesList()
                default['regexp'] = self.regExp
                log.debug("setModelData -> default = %s" % default)

                from code_saturne.Pages.VerifyExistenceLabelDialogView import VerifyExistenceLabelDialogView
                dialog = VerifyExistenceLabelDialogView(self.parent, default)
                if dialog.exec_():
                    result = dialog.get_result()
                    new_pname = result['name']
                    log.debug("setModelData -> result = %s" % result)
                else:
                    new_pname = self.old_pname

            model.setData(index, new_pname, Qt.DisplayRole)

#-------------------------------------------------------------------------------
# Line edit delegate for the chemical formula
#-------------------------------------------------------------------------------

class ChemicalFormulaDelegate(QItemDelegate):
    """
    Use of a QLineEdit in the table.
    """
    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)
        self.parent = parent
        self.old_pname = ""


    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        self.old_pname = ""
        rx = "[chonsCHONS()][CHONSchons()1-9]{0," + str(LABEL_LENGTH_MAX-1) + "}"
        self.regExp = QRegExp(rx)
        v = RegExpValidator(editor, self.regExp)
        editor.setValidator(v)
        return editor


    def setEditorData(self, editor, index):
        editor.setAutoFillBackground(True)
        value = from_qvariant(index.model().data(index, Qt.DisplayRole), to_text_string)
        self.old_pname = str(value)
        editor.setText(value)


    def setModelData(self, editor, model, index):
        if not editor.isModified():
            return

        if editor.validator().state == QValidator.Acceptable:
            new_pname = str(editor.text())

            if new_pname in model.mdl.getSpecieNamesList():
                default = {}
                default['name']  = self.old_pname
                default['list']   = model.mdl.getSpecieNamesList()
                default['regexp'] = self.regExp
                log.debug("setModelData -> default = %s" % default)

                from code_saturne.Pages.VerifyExistenceLabelDialogView import VerifyExistenceLabelDialogView
                dialog = VerifyExistenceLabelDialogView(self.parent, default)
                if dialog.exec_():
                    result = dialog.get_result()
                    new_pname = result['name']
                    log.debug("setModelData -> result = %s" % result)
                else:
                    new_pname = self.old_pname

            model.setData(index, new_pname, Qt.DisplayRole)

#-------------------------------------------------------------------------------
# Line edit delegate for the value
#-------------------------------------------------------------------------------

class ValueDelegate(QItemDelegate):
    def __init__(self, parent=None):
        super(ValueDelegate, self).__init__(parent)
        self.parent = parent


    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        v = DoubleValidator(editor, min=0.)
        editor.setValidator(v)
        return editor


    def setEditorData(self, editor, index):
        editor.setAutoFillBackground(True)
        value = from_qvariant(index.model().data(index, Qt.DisplayRole), to_text_string)
        editor.setText(value)


    def setModelData(self, editor, model, index):
        if not editor.isModified():
            return
        if editor.validator().state == QValidator.Acceptable:
            value = from_qvariant(editor.text(), float)
            for idx in self.parent.selectionModel().selectedIndexes():
                if idx.column() == index.column():
                    model.setData(idx, value, Qt.DisplayRole)


#-------------------------------------------------------------------------------
# StandarItemModel class
#-------------------------------------------------------------------------------

class StandardItemModelSpecies(QStandardItemModel):
    """
    """
    def __init__(self, parent, mdl):
        """
        """
        QStandardItemModel.__init__(self)

        self.headers = [self.tr("Specie"),
                        self.tr("Chemical Formula"),
                        self.tr("Fuel Composition"), 
                        self.tr("Oxidant Composition"), 
                        self.tr("Product Composition"), 
                        self.tr("Coeff absorption")]

        self.setColumnCount(len(self.headers))

        self._data = []
        self.parent = parent
        self.mdl  = mdl


    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            return self._data[row][col]

        return None


    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() != 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsSelectable


    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None


    def setData(self, index, value, role):
        if not index.isValid():
            return Qt.ItemIsEnabled

        # Update the row in the table
        row = index.row()
        col = index.column()

        # Label (nothing to do for the specie label)
        if col == 0:
            pass
            
        # Chemical formula
        elif col == 1:
            ChemicalFormula = str(from_qvariant(value, to_text_string))
            self._data[row][col] = ChemicalFormula
            label = self._data[row][0]
            self.mdl.setSpecieChemicalFormula(label, ChemicalFormula)

        # Fuel Composition
        elif col == 2:
            CompFuel = str(from_qvariant(value, to_text_string))
            self._data[row][col] = CompFuel
            label = self._data[row][0]
            self.mdl.setCompFuel(label, CompFuel)

        # Oxi Composition
        elif col == 3:
            CompOxi = str(from_qvariant(value, to_text_string))
            self._data[row][col] = CompOxi
            label = self._data[row][0]
            self.mdl.setCompOxi(label, CompOxi)

        # Product Composition
        elif col == 4:
            CompProd = str(from_qvariant(value, to_text_string))
            self._data[row][col] = CompProd
            label = self._data[row][0]
            self.mdl.setCompProd(label, CompProd)

        # Coeff absorption
        elif col == 5:
            CoeffAbsorp = str(from_qvariant(value, to_text_string))
            self._data[row][col] = CoeffAbsorp
            label = self._data[row][0]
            self.mdl.setCoeffAbsorp(label, CoeffAbsorp)

        self.dataChanged.emit(index, index)
        return True


    def getData(self, index):
        row = index.row()
        return self._data[row]


    def newItem(self, existing_name=None):
        """
        Add an item in the table view
        """
        row = self.rowCount()

        label = self.mdl.addSpecie(existing_name)

        ChemicalFormula = self.mdl.getSpecieChemicalFormula(label)
        CompFuel = self.mdl.getCompFuel(label)
        CompOxi = self.mdl.getCompOxi(label)
        CompProd = self.mdl.getCompProd(label)
        CoeffAbsorp = self.mdl.getCoeffAbsorp(label)
        
        specie = [label, ChemicalFormula, CompFuel, CompOxi, CompProd, CoeffAbsorp]

        self.setRowCount(row+1)
        self._data.append(specie)


    def getItem(self, row):
        """
        Return the values for an item.
        """
        [label, ChemicalFormula, CompFuel, CompOxi, CompProd, CoeffAbsorp] = self._data[row]
        return label, ChemicalFormula, CompFuel, CompOxi, CompProd, CoeffAbsorp


    def deleteItem(self, row):
        """
        Delete the row in the model.
        """
        log.debug("deleteItem row = %i " % row)

        del self._data[row]
        row = self.rowCount()
        self.setRowCount(row-1)


#-------------------------------------------------------------------------------
# Main class
#-------------------------------------------------------------------------------

class GasCombustionView(QWidget, Ui_GasCombustionForm):
    """
    Class to open the Gas Combustion option Page.
    """

    def __init__(self, parent, case):
        """
        Constructor
        """
        QWidget.__init__(self, parent)

        Ui_GasCombustionForm.__init__(self)
        self.setupUi(self)

        self.case = case
        self.case.undoStopGlobal()
        self.mdl = GasCombustionModel(self.case)
        self.thermodata = ThermochemistryData(self.case)

        # Model for table View
        self.modelSpecies = StandardItemModelSpecies(self, self.thermodata)
        self.tableViewSpecies.setModel(self.modelSpecies)

        # Delegates
        delegateLabel            = NameDelegate(self.tableViewSpecies)
        delegateChemicalFormula  = ChemicalFormulaDelegate(self.tableViewSpecies)
        delegateCompFuel  = ValueDelegate(self.tableViewSpecies)
        delegateCompOxi   = ValueDelegate(self.tableViewSpecies)
        delegateCompProd  = ValueDelegate(self.tableViewSpecies)
        delegateCoeffAbsorp  = ValueDelegate(self.tableViewSpecies)

        self.tableViewSpecies.setItemDelegateForColumn(0, delegateLabel)
        self.tableViewSpecies.setItemDelegateForColumn(1, delegateChemicalFormula)
        self.tableViewSpecies.setItemDelegateForColumn(2, delegateCompFuel)
        self.tableViewSpecies.setItemDelegateForColumn(3, delegateCompOxi)
        self.tableViewSpecies.setItemDelegateForColumn(4, delegateCompProd)
        self.tableViewSpecies.setItemDelegateForColumn(5, delegateCoeffAbsorp)

        # tableView
        if QT_API == "PYQT4":
            self.tableViewSpecies.horizontalHeader().setResizeMode(QHeaderView.Stretch)
            self.tableViewSpecies.horizontalHeader().setResizeMode(0,QHeaderView.ResizeToContents)
            self.tableViewSpecies.horizontalHeader().setResizeMode(1,QHeaderView.ResizeToContents)
        elif QT_API == "PYQT5":
            self.tableViewSpecies.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tableViewSpecies.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents)
            self.tableViewSpecies.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents)

        # Set models and number of elements for combo boxes
        self.modelGasCombustionOption = ComboModel(self.comboBoxGasCombustionOption,1,1)

        # Connections
        self.comboBoxGasCombustionOption.activated[str].connect(self.slotGasCombustionOption)
        self.pushButtonThermochemistryData.pressed.connect(self.__slotSearchThermochemistryData)
        self.radioButtonCreateJanafFile.clicked.connect(self.slotCreateJanafFile)
        self.lineEditNbPointsTabu.textChanged[str].connect(self.slotNbPointsTabu)
        self.lineEditMaximalTemp.textChanged[str].connect(self.slotMaximalTemp)
        self.lineEditMinimalTemp.textChanged[str].connect(self.slotMinimalTemp)
        self.pushButtonAddSpecie.clicked.connect(self.slotAddSpecie)
        self.pushButtonDeleteSpecie.clicked.connect(self.slotDeleteSpecie)
        self.pushButtonGenerateJanafFile.clicked.connect(self.slotGenerateJanafFile)
        self.modelSpecies.dataChanged.connect(self.dataChanged)

        # Validators
        validatorNbPointsTabu = IntValidator(self.lineEditNbPointsTabu, min=1)
        validatorMaximalTemp  = DoubleValidator(self.lineEditMaximalTemp, min=273.0)
        validatorMinimalTemp  = DoubleValidator(self.lineEditMinimalTemp, min=273.0)

        self.lineEditNbPointsTabu.setValidator(validatorNbPointsTabu)
        self.lineEditMaximalTemp.setValidator(validatorMaximalTemp)
        self.lineEditMinimalTemp.setValidator(validatorMinimalTemp)

        NbPointsTabu = self.thermodata.getNbPointsTabu()
        MaximalTemp  = self.thermodata.getMaximalTemp()
        MinimalTemp  = self.thermodata.getMinimalTemp()

        self.lineEditNbPointsTabu.setText(str(NbPointsTabu))
        self.lineEditMaximalTemp.setText(str(MaximalTemp))
        self.lineEditMinimalTemp.setText(str(MinimalTemp))

        # Initialize Widgets

        self.tableViewSpecies.reset()
        self.modelSpecies = StandardItemModelSpecies(self, self.thermodata)
        self.tableViewSpecies.setModel(self.modelSpecies)

        model = self.mdl.getGasCombustionModel()

        if model == 'd3p':
            self.modelGasCombustionOption.addItem(self.tr("adiabatic model"), "adiabatic")
            self.modelGasCombustionOption.addItem(self.tr("non adiabatic model"), "extended")
        elif model == 'ebu':
            self.modelGasCombustionOption.addItem(self.tr("reference Spalding model"), "spalding")
            self.modelGasCombustionOption.addItem(self.tr("extended model with enthalpy source term"), "enthalpy_st")
            self.modelGasCombustionOption.addItem(self.tr("extended model with mixture fraction transport"), "mixture_st")
            self.modelGasCombustionOption.addItem(self.tr("extended model with enthalpy and mixture fraction transport"), "enthalpy_mixture_st")
        elif model == 'lwp':
            self.modelGasCombustionOption.addItem(self.tr("reference two-peak model with adiabatic condition"), "2-peak_adiabatic")
            self.modelGasCombustionOption.addItem(self.tr("reference two-peak model with enthalpy source term"), "2-peak_enthalpy")
            self.modelGasCombustionOption.addItem(self.tr("reference three-peak model with adiabatic condition"), "3-peak_adiabatic")
            self.modelGasCombustionOption.addItem(self.tr("reference three-peak model with enthalpy source term"), "3-peak_enthalpy")
            self.modelGasCombustionOption.addItem(self.tr("reference four-peak model with adiabatic condition"), "4-peak_adiabatic")
            self.modelGasCombustionOption.addItem(self.tr("reference four-peak model with enthalpy source term"), "4-peak_enthalpy")

        option = self.mdl.getGasCombustionOption()
        self.modelGasCombustionOption.setItem(str_model= option)

        name = self.mdl.getThermoChemistryDataFileName()
        
        if name != "":
            self.labelThermochemistryFile.setText(str(name))
            self.pushButtonThermochemistryData.setStyleSheet("background-color: green")
        else:
            self.pushButtonThermochemistryData.setStyleSheet("background-color: red")

        self.radioButtonCreateJanafFile.hide()

        if self.thermodata.getCreateThermoDataFile() == 'on':
            self.radioButtonCreateJanafFile.setChecked(True)
        else:
            self.radioButtonCreateJanafFile.setChecked(False)

        # for the moment the option to create Janaf file in the GUI is only available with d3p (extended)
        if option == 'extended':
            self.radioButtonCreateJanafFile.show()
            self.groupBoxCreateJanafFile.show()

        self.slotCreateJanafFile()

        for label in self.thermodata.getSpecieNamesList():
            self.modelSpecies.newItem(label)

        self.case.undoStartGlobal()


    @pyqtSlot(str)
    def slotGasCombustionOption(self, text):
        """
        Private slot.
        Binding method for gas combustion models.
        """
        option = self.modelGasCombustionOption.dicoV2M[str(text)]
        self.mdl.setGasCombustionOption(option)
        # for the moment the option to create Janaf file in the GUI is only available with d3p (extended)
        if option == 'extended':
            self.radioButtonCreateJanafFile.show()
        else:
            self.radioButtonCreateJanafFile.setChecked(False)
            self.thermodata.setCreateThermoDataFile("off")
            self.radioButtonCreateJanafFile.hide()
            self.groupBoxCreateJanafFile.hide()

    @pyqtSlot()
    def __slotSearchThermochemistryData(self):
        """
        Select a properties file of data for electric arc
        """
        data = self.case['data_path']
        if not data:
            data = "."
        title = self.tr("Thermochemistry file of data.")
        filetypes = self.tr("Thermochemistry (*dp_*);;All Files (*)")
        file = QFileDialog.getOpenFileName(self, title, data, filetypes)[0]
        file = str(file)
        if not file:
            return
        file = os.path.basename(file)
        if file not in os.listdir(data):
            title = self.tr("WARNING")
            msg   = self.tr("This selected file is not in the DATA directory")
            QMessageBox.information(self, title, msg)
        else:
            self.labelThermochemistryFile.setText(str(file))
            self.mdl.setThermoChemistryDataFileName(file)
            self.pushButtonThermochemistryData.setStyleSheet("background-color: green")

    @pyqtSlot()
    def slotCreateJanafFile(self):
        """
        Determine if the Thermochemistry file is created with the GUI.
        """
        if self.radioButtonCreateJanafFile.isChecked():
            self.thermodata.setCreateThermoDataFile("on")
            self.groupBoxCreateJanafFile.show()
            self.lineEditNbPointsTabu.setText(str(self.thermodata.getNbPointsTabu()))
            self.lineEditMaximalTemp.setText(str(self.thermodata.getMaximalTemp()))
            self.lineEditMinimalTemp.setText(str(self.thermodata.getMinimalTemp()))
            return
        else:
            self.thermodata.setCreateThermoDataFile("off")
            self.groupBoxCreateJanafFile.hide()

    @pyqtSlot(str)
    def slotNbPointsTabu(self, text):
        """
        Input Number of points for the tabulation (ENTH-TEMP)
        """
        if self.lineEditNbPointsTabu.validator().state == QValidator.Acceptable:
            NbPointsTabu = from_qvariant(text, int)
            self.thermodata.setNbPointsTabu(NbPointsTabu)

    @pyqtSlot(str)
    def slotMaximalTemp(self, text):
        """
        Input Maximal temperature for the tabulation (ENTH-TEMP)
        """
        if self.lineEditMaximalTemp.validator().state == QValidator.Acceptable:
            MaximalTemp = from_qvariant(text, float)
            self.thermodata.setMaximalTemp(MaximalTemp)

    @pyqtSlot(str)
    def slotMinimalTemp(self, text):
        """
        Input Minimal temperature for the tabulation (ENTH-TEMP)
        """
        if self.lineEditMinimalTemp.validator().state == QValidator.Acceptable:
            MinimalTemp = from_qvariant(text, float)
            self.thermodata.setMinimalTemp(MinimalTemp)

    @pyqtSlot()
    def slotAddSpecie(self):
        """
        Add a new item in the table when the 'Create' button is pushed.
        """
        self.tableViewSpecies.clearSelection()
        self.modelSpecies.newItem()

    @pyqtSlot()
    def slotDeleteSpecie(self):
        """
        Just delete the current selected entries from the table and
        of course from the XML file.
        """
        lst = []
        for index in self.tableViewSpecies.selectionModel().selectedRows():
            row = index.row()
            lst.append(row)

        lst.sort()
        lst.reverse()

        for row in lst:
            label = self.modelSpecies.getItem(row)[0]
            self.thermodata.deleteSpecie(label)
            self.modelSpecies.deleteItem(row)

        self.tableViewSpecies.clearSelection()

    @pyqtSlot()
    def slotGenerateJanafFile(self):
        """
        Generate the Thermochemistry file.
        """

        data = self.case['data_path']
        if not data:
            data = "."
        filename = "dp_ThermochemistryFromGui"
        file_path = os.path.join(data, filename)

        self.thermodata.WriteThermochemistryDataFile(file_path)

        self.labelThermochemistryFile.setText(str(filename))
        self.mdl.setThermoChemistryDataFileName(filename)
        self.pushButtonThermochemistryData.setStyleSheet("background-color: green")


    @pyqtSlot("QModelIndex, QModelIndex")
    def dataChanged(self, topLeft, bottomRight):
        for row in range(topLeft.row(), bottomRight.row()+1):
            self.tableViewSpecies.resizeRowToContents(row)
        for col in range(topLeft.column(), bottomRight.column()+1):
            self.tableViewSpecies.resizeColumnToContents(col)


#-------------------------------------------------------------------------------
# Testing part
#-------------------------------------------------------------------------------


if __name__ == "__main__":
    pass


#-------------------------------------------------------------------------------
# End
#-------------------------------------------------------------------------------
