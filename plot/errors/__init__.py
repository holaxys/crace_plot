class PlotError(Exception):
    """Exceptions for crace-plot"""

    def __init__(self, message="No message provided."):
        super().__init__(message)
    pass


class OptionError(PlotError):
    """Exception for option type """
    def __init__(self, message="No message provided."):
        super().__init__(message)
    pass


class ParameterDefinitionError(PlotError):
    """Exception for option type """
    def __init__(self, message="No message provided."):
        super().__init__(message)
    pass


class ParameterValueError(PlotError):
    """Exception for option type """
    def __init__(self, message="No message provided."):
        super().__init__(message)
    pass


class ModelError(PlotError):
    """Exception for option type """
    def __init__(self, message="No message provided."):
        super().__init__(message)
    pass


class FileError(PlotError):
    """ Errors related to files (not found or invalid"""
    pass


class IraceExecutionError(PlotError):
    """
    Errors related to the execution of jobs
    """
    def __init__(self, message="No message provided."):
        super().__init__(message)
    pass
