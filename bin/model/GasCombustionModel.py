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
This module defines the gas combustion thermal flow modelling management.

This module contains the following classes and function:
- GasCombustionModel
- GasCombustionTestCase
- ThermochemistryData
"""

#-------------------------------------------------------------------------------
# Library modules import
#-------------------------------------------------------------------------------

import sys, unittest

#-------------------------------------------------------------------------------
# Application modules import
#-------------------------------------------------------------------------------

from code_saturne.model.Common import *
from code_saturne.model.XMLvariables import Variables, Model
from code_saturne.model.ThermalScalarModel import ThermalScalarModel
from code_saturne.model.TurbulenceModel import TurbulenceModel
from code_saturne.model.ThermalRadiationModel import ThermalRadiationModel
from code_saturne.model.FluidCharacteristicsModel import FluidCharacteristicsModel
from code_saturne.model.NumericalParamEquationModel import NumericalParamEquationModel
from code_saturne.model.LocalizationModel import LocalizationModel
from code_saturne.model.Boundary import Boundary

#-------------------------------------------------------------------------------
# Gas combustion model class
#-------------------------------------------------------------------------------

class GasCombustionModel(Variables, Model):
    """
    """
    def __init__(self, case):
        """
        Constructor.
        """
        self.case = case

        nModels          = self.case.xmlGetNode('thermophysical_models')
        self.node_turb   = nModels.xmlInitNode('turbulence',        'model')
        self.node_gas    = nModels.xmlInitNode('gas_combustion',    'model')
        self.node_coal   = nModels.xmlInitNode('solid_fuels',       'model')
        self.node_joule  = nModels.xmlInitNode('joule_effect',      'model')
        self.node_atmo   = nModels.xmlInitNode('atmospheric_flows', 'model')
        self.node_prop   = self.case.xmlGetNode('physical_properties')
        self.node_fluid  = self.node_prop.xmlInitNode('fluid_properties')

        self.gasCombustionModel = ('off', 'ebu', 'd3p','lwp')
        self.d3p_list = ("adiabatic", "extended")
        self.ebu_list = ("spalding", "enthalpy_st", "mixture_st", "enthalpy_mixture_st")
        self.lwp_list = ("2-peak_adiabatic", "2-peak_enthalpy",
                         "3-peak_adiabatic", "3-peak_enthalpy",
                         "4-peak_adiabatic", "4-peak_enthalpy")

        self.sootModels = ('off', 'soot_product_fraction', 'moss')


    def defaultGasCombustionValues(self):
        """
        Return in a dictionnary which contains default values.
        """
        default = {}
        default['model'] = "off"

        model = self.getGasCombustionModel()
        if model == 'd3p':
            default['option'] = "adiabatic"
        elif model == 'ebu':
            default['option'] = "spalding"
        elif model == 'lwp':
            default['option'] = "2-peak_adiabatic"
        elif model == 'off':
            default['option'] = "off"

        return default


    @Variables.noUndo
    def getAllGasCombustionModels(self):
        """
        Return all defined gas combustion models in a tuple.
        """
        return self.gasCombustionModel


    def gasCombustionModelsList(self):
        """
        Create a tuple with the available gas combustion models.
        """
        return self.gasCombustionModel


    @Variables.undoGlobal
    def setGasCombustionModel(self, model):
        """
        Update the gas combustion model markup from the XML document.
        """
        self.isInList(model, self.gasCombustionModelsList())
        node_prop   = self.case.xmlGetNode('physical_properties')
        node_fluid  = node_prop.xmlInitNode('fluid_properties')

        old_model = self.node_gas['model']
        ThermalScalarModel(self.case).setThermalModel('off')

        if model == 'off':
            self.node_gas['model'] = model
            self.node_gas['option'] = "off"
            ThermalRadiationModel(self.case).setRadiativeModel('off')
            for tag in ('variable',
                        'property',
                        'reference_mass_molar',
                        'reference_temperature',
                        'soot_model'):
                for node in self.node_gas.xmlGetNodeList(tag):
                    node.xmlRemoveNode()
            for zone in LocalizationModel('BoundaryZone', self.case).getZones():
                if zone.getNature() == "inlet":
                    Boundary("inlet", zone.getLabel(), self.case).deleteGas()

            node_fluid.xmlRemoveChild('property', name='dynamic_diffusion')

        else:
            self.node_gas['model'] = model
            self.node_coal['model']  = 'off'
            self.node_joule['model'] = 'off'
            self.setNewFluidProperty(node_fluid, 'dynamic_diffusion')

            if old_model != model:
                for zone in LocalizationModel('BoundaryZone', self.case).getZones():
                    if zone.getNature() == "inlet":
                        Boundary("inlet", zone.getLabel(), self.case).deleteGas()

        if model != 'd3p':
            self.node_fluid.xmlRemoveChild('reference_oxydant_temperature')
            self.node_fluid.xmlRemoveChild('reference_fuel_temperature')

        self.createModel()


    @Variables.noUndo
    def getGasCombustionModel(self):
        """
        Return the current gas combustion model.
        """
        model = self.node_gas['model']
        if model not in self.gasCombustionModelsList():
            model = 'off'
            self.setGasCombustionModel(model)

        return model


    @Variables.noUndo
    def getGasCombustionOption(self):
        """
        Return the current gas combustion option.
        """
        option = self.node_gas['option']
        if option == None:
            option = self.defaultGasCombustionValues()['option']
            self.setGasCombustionOption(option)

        model = self.getGasCombustionModel()
        if model == 'd3p':
            if option not in self.d3p_list:
                option = self.defaultGasCombustionValues()['option']
                self.setGasCombustionOption(option)
        elif model == 'ebu':
            if option not in self.ebu_list:
                option = self.defaultGasCombustionValues()['option']
                self.setGasCombustionOption(option)
        elif model == 'lwp':
            if option not in self.lwp_list:
                option = self.defaultGasCombustionValues()['option']
                self.setGasCombustionOption(option)
        elif model == 'off':
            option = 'off'
        return option


    @Variables.undoGlobal
    def setGasCombustionOption(self, option):
        """
        Return the current gas combustion option.
        """
        model = self.getGasCombustionModel()
        if model == 'd3p':
            self.isInList(option, self.d3p_list)
        elif model == 'ebu':
            self.isInList(option, self.ebu_list)
        elif model == 'lwp':
            self.isInList(option, self.lwp_list)
        elif model == 'off':
            self.isInList(option, ('off'))
        self.node_gas['option'] = option
        option = self.node_gas['option']
        self.createModel()


    def __createModelScalarsList(self , model):
        """
        Private method
        Create model scalar list
        """
        option = self.getGasCombustionOption()
        list_options = ["3-peak_adiabatic", "3-peak_enthalpy",
                        "4-peak_adiabatic", "4-peak_enthalpy"]
        acceptable_options = ["2-peak_enthalpy", "3-peak_enthalpy",
                              "4-peak_enthalpy"]
        lst = []

        ThermalScalarModel(self.case).setThermalModel('off')

        if model == 'd3p':
            lst.append("mixture_fraction")
            lst.append("mixture_fraction_variance")
            if option == 'extended':
                ThermalScalarModel(self.case).setThermalModel('enthalpy')
        elif model == 'ebu':
            lst.append("fresh_gas_fraction")
            if option == "mixture_st" or option =="enthalpy_mixture_st":
                lst.append("mixture_fraction")
            elif option == "enthalpy_st" or option =="enthalpy_mixture_st":
                ThermalScalarModel(self.case).setThermalModel('enthalpy')
        elif model == 'lwp':
            lst.append("mixture_fraction")
            lst.append("mixture_fraction_variance")
            lst.append("mass_fraction")
            lst.append("mass_fraction_covariance")
            if option in list_options:
                lst.append("mass_fraction_variance")
            if option in acceptable_options:
                ThermalScalarModel(self.case).setThermalModel('enthalpy')
        return lst


    def __createModelPropertiesList(self, model):
        """
        Private method
        Create model properties
        """
        lst = []
        lst.append("temperature")
        lst.append("ym_fuel")
        lst.append("ym_oxyd")
        lst.append("ym_prod")
        if model == 'lwp':
            lst.append("source_term")
            lst.append("molar_mass")
            ndirac = self.getNdirac()
            for idirac in range(ndirac):
                lst.append("rho_local_" + str(idirac + 1))
                lst.append("temperature_local_" + str(idirac + 1))
                lst.append("ym_local_" + str(idirac + 1))
                lst.append("w_local_" + str(idirac + 1))
                lst.append("amplitude_local_" + str(idirac + 1))
                lst.append("chemical_st_local_" + str(idirac + 1))
                lst.append("molar_mass_local_" + str(idirac + 1))
        return lst


    def __createModelScalars(self , model):
        """
        Private method
        Create model scalar
        """
        previous_list = []
        nodes = self.node_gas.xmlGetChildNodeList('variable')
        for node in nodes:
            previous_list.append(node['name'])

        if model == "off":
            for node in nodes:
                node.xmlRemoveNode()
        else:
            new_list = self.__createModelScalarsList(model)
            for name in previous_list:
                if name not in new_list:
                    self.node_gas.xmlRemoveChild('variable',  name = name)

            for name in new_list:
                if name not in previous_list:
                    self.setNewVariable(self.node_gas, name, tpe='var_model', label=name)

            NPE = NumericalParamEquationModel(self.case)
            for node in self.node_gas.xmlGetChildNodeList('variable'):
                name = node['name']
                NPE.setBlendingFactor(name, 0.)
                NPE.setScheme(name, 'upwind')
                NPE.setFluxReconstruction(name, 'off')

                if self.getGasCombustionModel() == "d3p":
                    if name == "mixture_fraction":
                        NPE.setMinValue(name, 0.)
                        NPE.setMaxValue(name, 1.)
                    elif name == "mixture_fraction_variance":
                        NPE.setMinValue(name, 0.)
                        NPE.setMaxValue(name, 1.e+12)
                        node.xmlSetData('variance', "mixture_fraction")


    @Variables.noUndo
    def getNdirac(self):
        """
        """
        option = self.getGasCombustionOption()
        self.isInList(option, self.lwp_list)
        if option == '2-peak_adiabatic' or option == '2-peak_enthalpy':
            ndirac = 2
        if option == '3-peak_adiabatic' or option == '3-peak_enthalpy':
            ndirac = 3
        if option == '4-peak_adiabatic' or option == '4-peak_enthalpy':
            ndirac = 4
        return ndirac


    def __createModelProperties(self, model):
        """
        Private method
        Create model properties
        """
        previous_list = []
        nodes = self.node_gas.xmlGetChildNodeList('property')
        if model == "off":
            for node in nodes:
                node.xmlRemoveNode()
        else:
            for node in nodes:
                previous_list.append(node['name'])

            new_list = self.__createModelPropertiesList(model)
            for name in previous_list:
                if name not in new_list:
                    self.node_gas.xmlRemoveChild('property',  name = name)

            for name in new_list:
                if name not in previous_list:
                    self.setNewProperty(self.node_gas, name)


    def createModel (self) :
        """
        Private method
        Create scalars and properties when gas combustion is selected
        """
        model = self.getGasCombustionModel()
        self.__createModelScalars(model)
        self.__createModelProperties(model)


    @Variables.noUndo
    def getThermoChemistryDataFileName(self):
        """
        Get name for properties data (return None if not defined)i
        """
        f = self.node_gas.xmlGetString('data_file')
        return f


    @Variables.undoLocal
    def setThermoChemistryDataFileName(self, name):
        """
        Put name for properties data and load file for number gaz and radiative model
        """
        self.node_gas.xmlSetData('data_file', name)

    def _defaultValues(self):
        """
        default values
        """
        self.default = {}
        self.default['thermodynamical_pressure'] = 'off'
        self.default['soot_model']               = 'off'
        self.default['soot_density']             = 0.0
        self.default['soot_fraction']            = 0.0
        return self.default

    @Variables.noUndo
    def getUniformVariableThermodynamicalPressure(self):
        """
        Return status of uniform variable thermodynamical pressure
        """
        node = self.node_gas.xmlInitNode('thermodynamical_pressure', 'status')
        status = node['status']
        if not status:
            status = self._defaultValues()['thermodynamical_pressure']
            self.setUniformVariableThermodynamicalPressure(status)
        return status

    @Variables.undoLocal
    def setUniformVariableThermodynamicalPressure(self, status):
        """
        Put status of uniform variable thermodynamical pressure
        """
        self.isOnOff(status)
        node = self.node_gas.xmlInitNode('thermodynamical_pressure', 'status')
        node['status'] = status

    @Variables.noUndo
    def getSootModel(self):
        """
        Return value of attribute model
        """
        node = self.node_gas.xmlInitChildNode('soot_model', 'model')
        model = node['model']
        if model not in self.sootModels:
            model = self._defaultValues()['soot_model']
            self.setSootModel(model)
        return model

    @Variables.undoGlobal
    def setSootModel(self, model):
        """
        Put value of attribute model to soot model
        """
        self.isInList(model, self.sootModels)
        node  = self.node_gas.xmlInitChildNode('soot_model', 'model')
        node['model'] = model
        if model == 'moss':
            self.node_gas.xmlRemoveChild('soot_fraction')
        if model == 'off':
            self.node_gas.xmlRemoveChild('soot_density')
            self.node_gas.xmlRemoveChild('soot_fraction')

    @Variables.noUndo
    def getSootDensity(self):
        """
        Return value of soot density
        """
        val = self.node_gas.xmlGetDouble('soot_density')
        if val == None:
            val = self._defaultValues()['soot_density']
            self.setSootDensity(val)
        return val

    @Variables.undoGlobal
    def setSootDensity(self, val):
        """
        Put value of soot density
        """
        self.isPositiveFloat(val)
        self.node_soot = self.node_gas.xmlGetNode('soot_model')
        self.node_soot.xmlSetData('soot_density', val)

    @Variables.noUndo
    def getSootFraction(self):
        """
        Return value of soot fraction
        """
        val = self.node_gas.xmlGetDouble('soot_fraction')
        if val == None:
            val = self._defaultValues()['soot_fraction']
            self.setSootFraction(val)
        return val

    @Variables.undoGlobal
    def setSootFraction(self, val):
        """
        Put value of soot fraction
        """
        self.isPositiveFloat(val)
        self.node_soot = self.node_gas.xmlGetNode('soot_model')
        self.node_soot.xmlSetData('soot_fraction', val)
#-------------------------------------------------------------------------------
# Gas combustion test case
#-------------------------------------------------------------------------------


class GasCombustionTestCase(unittest.TestCase):
    """
    """
    def setUp(self):
        """This method is executed before all "check" methods."""
        from code_saturne.model.XMLengine import Case, XMLDocument
        from code_saturne.model.XMLinitialize import XMLinit
        GuiParam.lang = 'en'
        self.case = Case(None)
        XMLinit(self.case).initialize()
        self.doc = XMLDocument()

    def tearDown(self):
        """This method is executed after all "check" methods."""
        del self.case
        del self.doc

    def xmlNodeFromString(self, string):
        """Private method to return a xml node from string"""
        return self.doc.parseString(string).root()

    def checkGasCombustionInstantiation(self):
        """
        Check whether the gasCombustionModel class could be instantiated
        """
        model = None
        model = GasCombustionModel(self.case)
        assert model != None, 'Could not instantiate GasCombustionModel'


def suite():
    testSuite = unittest.makeSuite(GasCombustionTestCase, "check")
    return testSuite


def runTest():
    print("GasCombustionTestCase - TODO**************")
    runner = unittest.TextTestRunner()
    runner.run(suite())

#-------------------------------------------------------------------------------
# Thermochemistry data class
#-------------------------------------------------------------------------------

class ThermochemistryData(Model):
    """
    Useful methods to create a Janaf File with the GUI
    """
    def __init__(self, case):

        """
        Constuctor.
        """
        self.case = case

        nModels              = self.case.xmlGetNode('thermophysical_models')
        self.node_thermodata = nModels.xmlInitNode('Thermochemistry_data')

        self.thermodatafile = ('off', 'on')
        self.nodes = ['NbPointsTabu', 'MaximalTemp', 'MinimalTemp']


    def defaultParamforTabu(self):
        """
        Return in a dictionnary which contains default values for the tabulation
        """
        default = {}
        default['CreateThermoDataFile'] = 'off'
        default['NbPointsTabu'] = 7
        default['MaximalTemp'] = 3000.0
        default['MinimalTemp'] = 273.0

        return default


    @Variables.noUndo
    def getCreateThermoDataFile(self):
        """
        Return status of CreateThermoDataFile
        """
        node = self.node_thermodata.xmlInitNode('CreateThermoDataFile', 'status')
        status = node['status']
        if not status:
            status = self.defaultParamforTabu()['CreateThermoDataFile']
            self.setCreateThermoDataFile(status)
        return status


    @Variables.undoLocal
    def setCreateThermoDataFile(self, status):
        """
        Put status of CreateThermoDataFile
        """
        self.isOnOff(status)
        node = self.node_thermodata.xmlInitNode('CreateThermoDataFile', 'status')
        node['status'] = status
        if status != 'on':
            self.node_thermodata.xmlRemoveChild('NbPointsTabu')
            self.node_thermodata.xmlRemoveChild('MaximalTemp')
            self.node_thermodata.xmlRemoveChild('MinimalTemp')
            nodes = self.node_thermodata.xmlGetChildNodeList('variable')
            for node in nodes:
                node.xmlRemoveNode()


    @Variables.noUndo
    def getNbPointsTabu(self, var):
        """
        Return value of NbPointsTabu for var
        """
        self.isInList(var, self.nodes)
        NbPointsTabu = self.node_thermodata.xmlGetInt(var)
        if NbPointsTabu == None:
            NbPointsTabu = self.defaultParamforTabu()['NbPointsTabu']
            self.setNbPointsTabu(var, NbPointsTabu)

        return NbPointsTabu


    @Variables.undoGlobal
    def setNbPointsTabu(self, txml, value):
        """
        Put value of NbPointsTabu for txml balise
        """
        self.isInList(txml, self.nodes)
        self.isInt(value)
        self.node_thermodata.xmlSetData(txml, value)


    @Variables.noUndo
    def getMaximalTemp(self, var):
        """
        Return value of MaximalTemp for var
        """
        self.isInList(var, self.nodes)
        MaximalTemp = self.node_thermodata.xmlGetDouble(var)
        if MaximalTemp == None:
            MaximalTemp = self.defaultParamforTabu()['MaximalTemp']
            self.setMinMaxTemp(var, MaximalTemp)

        return MaximalTemp


    @Variables.noUndo
    def getMinimalTemp(self, var):
        """
        Return value of MinimalTemp for var
        """
        self.isInList(var, self.nodes)
        MinimalTemp = self.node_thermodata.xmlGetDouble(var)
        if MinimalTemp == None:
            MinimalTemp = self.defaultParamforTabu()['MinimalTemp']
            self.setMinMaxTemp(var, MinimalTemp)

        return MinimalTemp


    @Variables.undoGlobal
    def setMinMaxTemp(self, txml, value):
        """
        Put value of Min Max temperature for txml balise
        """
        self.isInList(txml, self.nodes)
        self.isFloat(value)
        self.node_thermodata.xmlSetData(txml, value)


    def defaultSpeciesProperties(self):
        """
        Return the default properties for a specie
        """
        default = {}
        default['specie_label']         = "specie"
        default['chemical_formula']     = "CHON"
        default['stoich_coeff_fuel']    = 0.0
        default['stoich_coeff_oxi']     = 1.0
        default['coeff_absorption']     = 0.35

        return default


    def __defaultSpecieLabel(self, specie_name=None):
        """
        Private method.
        Return a default label for a new specie.
        """
        __coef = {}
        for l in self.getSpecieNamesList():
            __coef[l] = l
        length = len(__coef)
        Lspe = self.defaultSpeciesProperties()['specie_label']

        # new specie: default value 

        if not specie_name:
            if length != 0:
                i = 1
                while (Lspe + str(i)) in list(__coef.values()):
                    i = i + 1
                num = str(i)
            else:
                num = str(1)
            specie_name = Lspe + num
        return specie_name


    @Variables.undoGlobal
    def addSpecie(self, name=None):
        """
        Public method.
        Input a new specie I{name}
        """

        c = self.__defaultSpecieLabel(name)

        if c not in self.getSpecieNamesList():
            self.node_thermodata.xmlInitNode('variable', label=c, name=c)
            self.setSpecieChemicalFormula(c, self.defaultSpeciesProperties()['chemical_formula'])
            self.setStCoeffFuel(c, self.defaultSpeciesProperties()['stoich_coeff_fuel'])
            self.setStCoeffOxi(c, self.defaultSpeciesProperties()['stoich_coeff_oxi'])
            self.setCoeffAbsorp(c, self.defaultSpeciesProperties()['coeff_absorption'])

        return c


    @Variables.undoGlobal
    def deleteSpecie(self, specie_label):
        """
        Public method.
        Delete specie I{name}
        """
        self.isInList(specie_label, self.getSpecieNamesList())
        node = self.node_thermodata.xmlGetNode('variable', label=specie_label)
        node.xmlRemoveNode()


    @Variables.noUndo
    def getSpecieNamesList(self):
        """
        Public method.
        Return the Specie name list
        """
        lst = []
        for node in self.node_thermodata.xmlGetChildNodeList('variable'):
                lst.append(node['label'])
#                lst.append(node['name'])
        return lst


    @Variables.noUndo
    def getSpecieChemicalFormula(self, l):
        """
        Public method.
        Return the Chemical Formula
        """
        n = self.case.xmlGetNode('variable', label=l)
        name = n.xmlGetString('chemical_formula')
        return name


    @Variables.undoGlobal
    def setSpecieChemicalFormula(self, specie_label, specie_name):
        """
        Put the Chemical Formula
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('chemical_formula', specie_name)


    @Variables.undoGlobal
    def getStCoeffFuel(self, l):
        """
        Get stoichiometric coefficient (if fuel)
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('stoich_coeff_fuel')
        if val == None:
            val = self.defaultParamforTabu()['stoich_coeff_fuel']
            self.setStCoeffFuel(l, val)

        return val


    @Variables.undoGlobal
    def setStCoeffFuel(self, specie_label, StCoeffFuel):
        """
        Put stoichiometric coefficient (if fuel)
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('stoich_coeff_fuel', StCoeffFuel)


    @Variables.undoGlobal
    def getStCoeffOxi(self, l):
        """
        Get stoichiometric coefficient (if Oxi)
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('stoich_coeff_oxi')
        if val == None:
            val = self.defaultParamforTabu()['stoich_coeff_oxi']
            self.setStCoeffOxi(l, val)

        return val


    @Variables.undoGlobal
    def setStCoeffOxi(self, specie_label, StCoeffOxi):
        """
        Put stoichiometric coefficient (if Oxi)
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('stoich_coeff_oxi', StCoeffOxi)


    @Variables.undoGlobal
    def getCoeffAbsorp(self, l):
        """
        Get absorption coefficient
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('coeff_absorption')
        if val == None:
            val = self.defaultParamforTabu()['coeff_absorption']
            self.setCoeffAbsorp(l, val)

        return val


    @Variables.undoGlobal
    def setCoeffAbsorp(self, specie_label, CoeffAbsorp):
        """
        Put absorption coefficient
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('coeff_absorption', CoeffAbsorp)


#-------------------------------------------------------------------------------
# End
#-------------------------------------------------------------------------------
