import os
import sys
import json

from plot.errors import PlotError, OptionError, FileError, ParameterValueError
from plot.containers.parameters import IntegerParameter, RealParameter, CategoricalParameter, OrderedParameter

""" 
Variable that defines parameter types
  "i": integer 
  "r": real
  "c": categorical
  "o": ordered
  "i,log": logarithmic integer  
  "r,log": logarithmic real

"""
_parameter_types = ["i", "r", "c", "o", "i,log", "r,log"]

# In Crace plot, only "name", "type" and "domain" are used 
_regular_parameters = ["name", "switch", "type", "domain", "condition", "priority", "depends"]


def parameter_decoder(obj):
    """
    instantiates the correct class for a parameter
    :param obj: parameter (dictionary) obtained from the json settings definition
    :return: an instance of the Parameter class
    :raises OptionError: if type attribute is not found in obj or if type was not recognized
    """
    o = None
    if obj['type'] == 'i':
        o = IntegerParameter(obj)
    if obj['type'] == 'r':
        o = RealParameter(obj)
    if obj['type'] == 'c':
        o = CategoricalParameter(obj)
    if obj['type'] == 'o':
        o = OrderedParameter(obj)
    if o is None:
        raise OptionError("Parameter cannot be read: " + obj['name'])
    return o

class ReadParameters:
    """
    Read parameters for the provided Crace results
    """
    def __init__(self, file):
        """
        Initialization of an ReadParameters object. 
        The file of parameters.log must be provided.

        :param file: the parameters.log
        """
        
        # load parameters definition from json variable
        with open(file, "r") as read_file:
            all_parameters = json.loads(read_file.read(), object_hook=parameter_decoder)
        parameters = []
        for p in all_parameters:
            parameters.append(p.name)

    def get_parameter(self, parameter_name):
        """
        get a parameter in the ReadParameter object
        :param parameter_name: name of the parameter to be returned
        :return: value of the parameter
        :raises OptionError: if the parameter name is unknown
        """
        if parameter_name not in self.parameters:
            raise OptionError("Attempt to get unknown parameter " + parameter_name)
        return getattr(self, parameter_name)

    def set_parameter(self, parameter_name, parameter_value):
        """
        set the value of an parameter in the LoadParameters object
        :param parameter_name: name of the parameter
        :param parameter_value: value to be set
        :return: none
        :raises OptionError: if the parameter name is unknown
        """
        if parameter_name not in self.parameters:
            raise OptionError("Attempt to set unknown parameter " + parameter_name + " with value " + parameter_value)
        getattr(self, parameter_name).set_value(parameter_value)


    def is_set(self):
        return not (self.value is None)




