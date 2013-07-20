#  ============================================================================
#
#  Copyright (C) 2007-2013 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / info@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact info@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  info@conceptive.be
#
#  ============================================================================

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.view.proxy import ValueLoading
from ...art import Icon
from .customeditor import AbstractCustomEditor

LOGGER = logging.getLogger('camelot.view.controls.editors.ChoicesEditor')

class ChoicesEditor( QtGui.QComboBox, AbstractCustomEditor ):
    """A ComboBox aka Drop Down box that can be assigned a list of
    keys and values"""

    editingFinished = QtCore.pyqtSignal()
    valueChanged = QtCore.pyqtSignal()
    
    def __init__( self, 
                  parent = None, 
                  nullable = True, 
                  field_name = 'choices', 
                  **kwargs ):
        QtGui.QComboBox.__init__(self, parent)
        AbstractCustomEditor.__init__(self)
        self.setObjectName( field_name )
        self.activated.connect( self._activated )
        self._nullable = nullable 

    @QtCore.pyqtSlot(int)
    def _activated(self, _index):
        self.setProperty( 'value', QtCore.QVariant( self.get_value() ) )
        self.valueChanged.emit()
        self.editingFinished.emit()

    @staticmethod
    def append_item( model, data ):
        """Append an item in a combobox model
        :param data: a dictionary mapping roles to values
        """
        model.insertRow(model.rowCount())
        
        for role, value in data.iteritems():
            index = model.index(model.rowCount()-1, 0)
            if isinstance(value, Icon):
                value = value.getQIcon()
            model.setData(index, QtCore.QVariant(value), role)
        
    def set_choices( self, choices ):
        """
    :param choices: a list of (value,name) tuples or a list of dicts.
    
        In case a list of tuples is used, name will be displayed in the combobox,
        while value will be used within :meth:`get_value` and :meth:`set_value`.  
        
        In case a list of dicts is used, the keys of the dict are used as the
        roles, and the values as the value for that role, where `Qt.UserRole`
        is the value that is passed through :meth:`get_value`, 
        eg : `{Qt.DisplayRole: "Hello", Qt.UserRole: 1}`
        
        This method changes the items in the combo box while preserving the 
        current value, even if this value is not in the new list of choices.  
        If there is no item with value `None` in the list of choices, this will 
        be added.
        """
        current_index = self.currentIndex()
        if current_index >= 0:
            current_name = unicode(self.itemText(current_index))
        current_value = self.get_value()
        current_value_available = False
        none_available = False
        # set i to -1 to handle case of no available choices
        i = -1
        for i in range(self.count(), 0, -1):
            self.removeItem(i-1)
        model = self.model()
        for choice in choices:
            if not isinstance(choice, dict):
                (value, name) = choice
                font = QtGui.QFont()
                font.setItalic(True)
                choice = {Qt.DisplayRole: unicode(name),
                          Qt.UserRole: value}
            else:
                value = choice[Qt.UserRole]
            self.append_item(model, choice)
            if value == current_value:
                current_value_available = True
            if value == None:
                none_available = True
        if not current_value_available and current_index > 0:
            self.append_item(model, {Qt.DisplayRole: current_name,
                                     Qt.UserRole: current_value})
        if not none_available and current_value!=None:
            self.append_item(model, {Qt.DisplayRole: '',
                                     Qt.UserRole: None})
        # to prevent loops in the onetomanychoices editor, only set the value
        # again when it's not valueloading
        if current_value != ValueLoading:
            self.set_value( current_value )

    def set_field_attributes(self, editable=True, choices=None, **kwargs):
        if choices != None:
            self.set_choices(choices)
        self.setEnabled(editable!=False)

    def get_choices(self):
        """
    :rtype: a list of (value,name) tuples
    """
        from camelot.core.utils import variant_to_pyobject
        return [(variant_to_pyobject(self.itemData(i)),
                 unicode(self.itemText(i))) for i in range(self.count())]

    def set_value(self, value):
        """Set the current value of the combobox where value, the name displayed
        is the one that matches the value in the list set with set_choices"""
        from camelot.core.utils import variant_to_pyobject
        value = AbstractCustomEditor.set_value(self, value)
        self.setProperty( 'value', QtCore.QVariant(value) )
        self.valueChanged.emit()
        if not self.property('value_loading').toBool() and value != NotImplemented:
            for i in range(self.count()):
                if value == variant_to_pyobject(self.itemData(i)):
                    self.setCurrentIndex(i)
                    return
            # it might happen, that when we set the editor data, the set_choices
            # method has not happened yet or the choices don't contain the value
            # set
            self.setCurrentIndex( -1 )
            LOGGER.error( u'Could not set value %s in field %s because it is not in the list of choices'%( unicode( value ),
                                                                                                           unicode( self.objectName() ) ) )

    def get_value(self):
        """Get the current value of the combobox"""
        from camelot.core.utils import variant_to_pyobject
        current_index = self.currentIndex()
        if current_index >= 0:
            value = variant_to_pyobject(self.itemData(self.currentIndex()))
        else:
            value = ValueLoading
        return AbstractCustomEditor.get_value(self) or value

