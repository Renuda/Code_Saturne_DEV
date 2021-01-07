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

        # Parameters to create the Thermochemistry Data File
        # Available Chemical Elements
        self.ChemicalElem = ['C', 'H', 'O', 'N']
        # Molar mass for the Chemical Elements
        self.MolarMass = {}
        self.MolarMass['C'] = 0.012
        self.MolarMass['H'] = 0.001
        self.MolarMass['O'] = 0.016
        self.MolarMass['N'] = 0.014
        # Number of known global species, always 2 for the moment (Fuel and Oxy)
        # 2 -> Automatic equilibrium of the reaction
        self.NumberOfKnownGlobalSpecies = 2


    def defaultParamforTabu(self):
        """
        Return in a dictionnary which contains default values for the tabulation
        """
        default = {}
        default['CreateThermoDataFile'] = 'off'
        default['NbPointsTabu'] = 10
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
    def getNbPointsTabu(self):
        """
        Return value of NbPointsTabu
        """
        NbPointsTabu = self.node_thermodata.xmlGetInt('NbPointsTabu')
        if NbPointsTabu == None:
            NbPointsTabu = self.defaultParamforTabu()['NbPointsTabu']
            self.setNbPointsTabu(NbPointsTabu)

        return NbPointsTabu


    @Variables.undoGlobal
    def setNbPointsTabu(self, value):
        """
        Put value of NbPointsTabu
        """
        self.isInt(value)
        self.node_thermodata.xmlSetData('NbPointsTabu', value)


    @Variables.noUndo
    def getMaximalTemp(self):
        """
        Return value of MaximalTemp
        """
        MaximalTemp = self.node_thermodata.xmlGetDouble('MaximalTemp')
        if MaximalTemp == None:
            MaximalTemp = self.defaultParamforTabu()['MaximalTemp']
            self.setMaximalTemp(MaximalTemp)

        return MaximalTemp


    @Variables.undoGlobal
    def setMaximalTemp(self, value):
        """
        Put value of MaximalTemp
        """
        self.isFloat(value)
        self.node_thermodata.xmlSetData('MaximalTemp', value)


    @Variables.noUndo
    def getMinimalTemp(self):
        """
        Return value of MinimalTemp
        """
        MinimalTemp = self.node_thermodata.xmlGetDouble('MinimalTemp')
        if MinimalTemp == None:
            MinimalTemp = self.defaultParamforTabu()['MinimalTemp']
            self.setMinimalTemp(MinimalTemp)

        return MinimalTemp


    @Variables.undoGlobal
    def setMinimalTemp(self, value):
        """
        Put value of MinimalTemp
        """
        self.isFloat(value)
        self.node_thermodata.xmlSetData('MinimalTemp', value)


    def defaultSpeciesProperties(self):
        """
        Return the default properties for a specie
        """
        default = {}
        default['specie_label']         = "specie"
        default['chemical_formula']     = "CHON"
        default['fuel_composition']    = 0.0
        default['oxi_composition']     = 0.0
        default['prod_composition']     = 0.0
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
            self.setCompFuel(c, self.defaultSpeciesProperties()['fuel_composition'])
            self.setCompOxi(c, self.defaultSpeciesProperties()['oxi_composition'])
            self.setCompProd(c, self.defaultSpeciesProperties()['prod_composition'])
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
    def getCompFuel(self, l):
        """
        Get Fuel Composition
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('fuel_composition')
        if val == None:
            val = self.defaultSpeciesProperties()['fuel_composition']
            self.setCompFuel(l, val)

        return val


    @Variables.undoGlobal
    def setCompFuel(self, specie_label, CompFuel):
        """
        Put Fuel Composition
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('fuel_composition', CompFuel)


    @Variables.undoGlobal
    def getCompOxi(self, l):
        """
        Get Oxi Composition
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('oxi_composition')
        if val == None:
            val = self.defaultSpeciesProperties()['oxi_composition']
            self.setCompOxi(l, val)

        return val


    @Variables.undoGlobal
    def setCompOxi(self, specie_label, CompOxi):
        """
        Put Oxi Composition
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('oxi_composition', CompOxi)


    @Variables.undoGlobal
    def getCompProd(self, l):
        """
        Get Product Composition
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('prod_composition')
        if val == None:
            val = self.defaultSpeciesProperties()['prod_composition']
            self.setCompProd(l, val)

        return val


    @Variables.undoGlobal
    def setCompProd(self, specie_label, CompProd):
        """
        Put Product Composition
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('prod_composition', CompProd)


    @Variables.undoGlobal
    def getCoeffAbsorp(self, l):
        """
        Get absorption coefficient
        """
        n = self.case.xmlGetNode('variable', label=l)
        val = n.xmlGetDouble('coeff_absorption')
        if val == None:
            val = self.defaultSpeciesProperties()['coeff_absorption']
            self.setCoeffAbsorp(l, val)

        return val


    @Variables.undoGlobal
    def setCoeffAbsorp(self, specie_label, CoeffAbsorp):
        """
        Put absorption coefficient
        """
        n = self.case.xmlGetNode('variable', label=specie_label)
        n.xmlSetData('coeff_absorption', CoeffAbsorp)


    @Variables.undoGlobal
    def getNumberOfChemicalElem(self, ChemicalFormula):
        """
        Get the number of Chemical Element
        """

        ChemicalFormula = str(ChemicalFormula.upper())
        
        NumberOfChemElem = {}
        for Elem in self.ChemicalElem:
            NumberOfChemElem[Elem] = "0"
        
        for Elem in self.ChemicalElem :
            ReadFirstElem = True
            Current_Elem = ""

            for char in ChemicalFormula :

                if char == Elem :
                    NumberOfChemElem[Elem] = "1"
                    ReadFirstElem = True

                if char.isdigit() and Current_Elem == Elem:
                    if ReadFirstElem : 
                        ReadFirstElem = False
                        NumberOfChemElem[Elem] = ""
                    NumberOfChemElem[Elem] = NumberOfChemElem[Elem]+char
                
                if not char.isdigit(): Current_Elem = char

        return NumberOfChemElem

    @Variables.undoGlobal
    def WriteThermochemistryDataFile(self, file_path):
        """
        Write the thermochemistry Data File
        """

        #Comment to add at the end of each lines FR
        InfoLine = {}
        InfoLine['NumberOfSpecies'] = "Nb especes courantes"
        InfoLine['NbPointsTabu'] = "Nb de points de tabulation ENTH-TEMP"
        InfoLine['MinimalTemp'] = "TMIN"
        InfoLine['MaximalTemp'] = "TMAX"
        InfoLine['LineInfo-GaseousSpecies'] = "Especes Gazeuses"
        InfoLine['CoeffAbsorp'] = "Coeff absorption (ray)"
        InfoLine['GlobalElemCompo'] = "Nb especes elementaires"
        InfoLine['LineInfo-ChemElem'] = "Composition CHON"
        InfoLine['NumberOfKnownGlobalSpecies'] = "Nb d'especes globales connues (ici : / Fuel / Oxydant / Produits)"
        InfoLine['FuelComposition'] = "Numero espece reactive / Composition Fuel     en especes elementaires"
        InfoLine['OxiComposition'] = "Numero espece reactive / Composition Oxydant  en especes elementaires"
        InfoLine['ProdComposition'] = "Numero espece reactive / Composition Produits en especes elementaires"

        #Open the Thermochemistry Data File
        f = open(file_path, "w")
        
        # Write the number of species, and parameters for the tabulation ENTH TEMP
        NumberOfSpecies = len(self.getSpecieNamesList())
        NbPointsTabu = self.getNbPointsTabu()
        MinimalTemp  = self.getMinimalTemp()
        MaximalTemp  = self.getMaximalTemp()
        f.write('{:<10}'.format(str(NumberOfSpecies))+InfoLine['NumberOfSpecies']+"\n")
        f.write('{:<10}'.format(str(NbPointsTabu))+InfoLine['NbPointsTabu']+"\n")
        f.write('{:<10}'.format(str(MinimalTemp))+InfoLine['MinimalTemp']+"\n")
        f.write('{:<10}'.format(str(MaximalTemp))+InfoLine['MaximalTemp']+"\n")
        f.write(InfoLine['LineInfo-GaseousSpecies']+"\n")
        f.write(" "*10)

        # Reorder the species to have the Fuel in first, then Oxidant and 
        # finish by the Product and sorted the compositions (see colecd.f90)
        maxCompFuel = 0.0
        maxCompOxi  = 0.0
        maxCompProd = 0.0
        for label in self.getSpecieNamesList():
            maxCompFuel = max(maxCompFuel, self.getCompFuel(label))
            maxCompOxi = max(maxCompOxi, self.getCompOxi(label))
            maxCompProd = max(maxCompProd, self.getCompProd(label))

        Order = []
        for i in range(NumberOfSpecies):
            Order.append(3)

        i = 0
        for label in self.getSpecieNamesList():
            if self.getCompFuel(label) > 0.0:
                Order[i] = 0 + self.getCompFuel(label)/maxCompFuel
            if self.getCompOxi(label) > 0.0:
                Order[i] = 1 + self.getCompOxi(label)/maxCompOxi
            if self.getCompProd(label) > 0.0:
                Order[i] = 3 + self.getCompProd(label)/maxCompProd
            i = i + 1
      
        getSpecieNamesList_Sorted = self.getSpecieNamesList()
        Order, getSpecieNamesList_Sorted = zip(*sorted(zip(Order, getSpecieNamesList_Sorted)))

        # Write the chemical formula of all the species
        for label in getSpecieNamesList_Sorted:
            ChemicalFormula = self.getSpecieChemicalFormula(label)
            f.write('{:>15}'.format(str(ChemicalFormula).upper()))
        f.write("\n")
        f.write(" "*10)

        # Write the absoption coefficient for all the species
        for label in getSpecieNamesList_Sorted:
            CoeffAbsorp = self.getCoeffAbsorp(label)
            f.write('{:>15}'.format(str(CoeffAbsorp)))
        f.write(" "*5+InfoLine['CoeffAbsorp']+"\n")

        # List of all chemical formula
        LstChemicalFormula = []
        for label in getSpecieNamesList_Sorted:
            LstChemicalFormula.append(str(self.getSpecieChemicalFormula(label)))

        # Write the number of chemical element (CHON)
        GlobalElemCompo = {}
        for Elem in self.ChemicalElem:
            GlobalElemCompo[Elem] = False
        for Elem in self.ChemicalElem:
            if Elem in str(LstChemicalFormula):
                GlobalElemCompo[Elem] = True
        f.write('{:<15}'.format(str(str(GlobalElemCompo).count("True")))+" "*15*NumberOfSpecies+InfoLine['GlobalElemCompo']+"\n")

        # Create a dictionnary with the composition in chemical elements for each specie
        Composition = {}
        for label in getSpecieNamesList_Sorted:
            ChemicalFormula = self.getSpecieChemicalFormula(label)
            Composition[ChemicalFormula] = self.getNumberOfChemicalElem(ChemicalFormula)

        # Write the number of chemical element (CHON) for each specie
        for Elem in self.ChemicalElem:
            if GlobalElemCompo[Elem] == True:
                f.write('{:<10}'.format(str(self.MolarMass.get(Elem))))
                for label in getSpecieNamesList_Sorted:
                    ChemicalFormula = self.getSpecieChemicalFormula(label)
                    f.write('{:>15}'.format(str(Composition[ChemicalFormula][Elem])))
                if Elem == self.ChemicalElem[0]:
                    f.write(" "*5+InfoLine['LineInfo-ChemElem'])
                f.write('\n')

        # Write the number of known global species (always 2 (Fuel and Oxy) for the moment)
        f.write('{:<15}'.format(str(self.NumberOfKnownGlobalSpecies))+" "*15*NumberOfSpecies+InfoLine['NumberOfKnownGlobalSpecies']+"\n")
        f.write(" "*10)

        #Write the Fuel composition
        for label in getSpecieNamesList_Sorted:
            f.write('{:>15}'.format(str(self.getCompFuel(label))))
        f.write(" "*5+InfoLine['FuelComposition']+"\n")
        f.write(" "*10)

        #Write the Oxidant composition
        for label in getSpecieNamesList_Sorted:
            f.write('{:>15}'.format(str(self.getCompOxi(label))))
        f.write(" "*5+InfoLine['OxiComposition']+"\n")
        f.write(" "*10)

        #Write the Product composition
        for label in getSpecieNamesList_Sorted:
            f.write('{:>15}'.format(str(self.getCompProd(label))))
        f.write(" "*5+InfoLine['ProdComposition'])

        #Close the Thermochemistry Data File
        f.close()

#-------------------------------------------------------------------------------
# End
#-------------------------------------------------------------------------------
