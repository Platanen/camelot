from camelot.container import Container
from matplotlib import axes

class FigureContainer( Container ):
    """A container that is able to plot itself on a matplotlib figure canvas.
    
    Its 'plot_on_figure' method will be called in the gui thread to fill the figure
    canvas.
    
    One figure canvas can contain multiple axes (=sub plots)
    """
    
    def __init__(self, axes):
        """
        :param axes: a list of AxesContainer objects representing all the subplots, in
        the form of ::
        
          [[ax1, ax2],
           [ax3, ax4]]
           
        """
        self.axes = axes
        
    def plot_on_figure(self, fig):
        """Draw all axes (sub plots) on a figure canvas"""
        fig.clear()
        if self.axes:
            rows = len(self.axes)
            cols = len(self.axes[0])
            for i,row in enumerate(self.axes):
                for j,subplot in enumerate(row):
                    n = i*cols + j
                    ax = fig.add_subplot( rows, cols, n+1 )
                    ax.clear()
                    subplot.plot_on_axes( ax )
                
class AxesMethod(object):
    """Helper class to substitute a method on an Axes object and
    record its calls"""
    
    def __init__(self, method_name, commands):
        """
        :param method_name: the name of the method for which this object is a substitute
        :param commands: a list in which to store invocations of the method
        """
        self._method_name = method_name
        self._commands = commands
        
    def __call__(self, *args, **kwargs):
        """record a call the the substitute method into the commands list"""
        self._commands.append( (self._method_name, args, kwargs) )
            
class AxesContainer( Container ):
    """A container that is able to generate a plot on a matplotlib axes.  Methods
    can be called on this class as if it were a matplotlib Axes class.  All method
    calls will be recorded.  Of course the methods won't return matplotlib objects."""

    def __init__(self):
        super(AxesContainer, self).__init__()
        # store all the method calls that need to be called on a
        # matplotlib axes object in a list
        self._commands = list()
        
    def __getattr__(self, attribute_name):
        """Suppose the caller wants to call a function on a matplotlib
        axes object"""
        return AxesMethod( attribute_name, self._commands )
        
    def plot_on_axes(self, ax):
        """Replay the list of stored commands to the real Axes object"""
        for name, args, kwargs in self._commands:
            getattr(ax, name)(*args, **kwargs)

class PlotContainer( AxesContainer ):

    __doc__ = axes.Axes.plot.__doc__
    
    def __init__(self, *args, **kwargs):
        """:param *args: the arguments to be passed to the matplotlib plot command"""
        super(PlotContainer, self).__init__()
        self.plot( *args, **kwargs )
        
class BarContainer( AxesContainer ):

    __doc__ = axes.Axes.bar.__doc__
    
    def __init__(self, *args, **kwargs):
        """:param *args: the arguments to be passed to the matplotlib bar command"""
        super(BarContainer, self).__init__()
        self.bar( *args, **kwargs )
                    
def structure_to_figure_container( structure ):
    """Convert a structure to a figure container, if the structure
    is an instance of a FigureContainer, return as is.
    
    If the structure is an instance of an AxesContainer, return a
    FigureContainer with a single Axes.
    
    If the structure is a list, use the structure as a constructor
    argument for the FigureContainer
    """
    
    if isinstance(structure, FigureContainer):
        return structure
    if isinstance(structure, AxesContainer):
        return FigureContainer( [[structure]] )
    if isinstance(structure, (list, tuple)):
        return FigureContainer( structure )
