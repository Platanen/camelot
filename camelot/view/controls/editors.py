#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Editors for various type of values"""
import os
import os.path
import tempfile
import logging
import settings

logger = logging.getLogger('editors')

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from camelot.view import art
from camelot.view.model_thread import model_function

class DateEditor(QtGui.QWidget):
  """Widget for editing date values"""
  def __init__(self, nullable=True, format='dd/MM/yyyy', parent=None):
    super(DateEditor, self).__init__(parent)
    self.format = format
    self.qdateedit = QtGui.QDateEdit(self)
    self.connect(self.qdateedit, QtCore.SIGNAL('editingFinished ()'), self.editingFinished)
    self.qdateedit.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.qdateedit.setDisplayFormat(QtCore.QString(format))
    self.hlayout = QtGui.QHBoxLayout()
    self.hlayout.addWidget(self.qdateedit)
    
    if nullable:
      nullbutton = QtGui.QToolButton()
      nullbutton.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
      nullbutton.setAutoRaise(True)
      #nullbutton.setCheckable(True)
      self.connect(nullbutton, QtCore.SIGNAL('clicked()'), self.setMinimumDate)
      self.qdateedit.setSpecialValueText('0/0/0')
      self.hlayout.addWidget(nullbutton)
          
    self.hlayout.setContentsMargins(0, 0, 0, 0)
    self.hlayout.setMargin(0)
    self.hlayout.setSpacing(0)

    self.setContentsMargins(0, 0, 0, 0)
    self.setLayout(self.hlayout)

    import datetime
    self.minimum = datetime.date.min
    self.maximum = datetime.date.max
    self.set_date_range()

    self.setFocusProxy(self.qdateedit)

  def _python_to_qt(self, value):
    return QtCore.QDate(value.year, value.month, value.day)

  def _qt_to_python(self, value):
    import datetime
    return datetime.date(value.year(), value.month(), value.day())
  
  def editingFinished(self):
    self.emit(QtCore.SIGNAL('editingFinished()'))
      
  def set_date_range(self):
    qdate_min = self._python_to_qt(self.minimum)
    qdate_max = self._python_to_qt(self.maximum)
    self.qdateedit.setDateRange(qdate_min, qdate_max)

  def date(self):
    return self.qdateedit.date()

  def minimumDate(self):
    return self.qdateedit.minimumDate()

  def setMinimumDate(self):
    self.qdateedit.setDate(self.minimumDate())
    self.emit(QtCore.SIGNAL('editingFinished()'))

  def setDate(self, date):
    self.qdateedit.setDate(date)

class VirtualAddressEditor(QtGui.QWidget):
  
  def __init__(self, parent=None):
    import camelot.types
    super(VirtualAddressEditor, self).__init__(parent)
    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    self.combo = QtGui.QComboBox()
    self.combo.addItems(camelot.types.VirtualAddress.virtual_address_types)
    layout.addWidget(self.combo)
    self.editor = QtGui.QLineEdit()
    layout.addWidget(self.editor)
    self.connect(self.editor, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    self.setLayout(layout)
  def editingFinished(self):
    self.emit(QtCore.SIGNAL('editingFinished()'))
        
class CodeEditor(QtGui.QWidget):
  
  def __init__(self, parts=['99', 'AA'], parent=None):
    super(CodeEditor, self).__init__(parent)
    self.setFocusPolicy(Qt.StrongFocus)
    self.parts = parts
    self.part_editors = []
    layout = QtGui.QHBoxLayout()
    #layout.setSpacing(0)
    layout.setMargin(0)
    for part in parts:
      editor = QtGui.QLineEdit()
      editor.setInputMask(part)
      editor.installEventFilter(self)
      self.part_editors.append(editor)
      layout.addWidget(editor)
      self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    self.setLayout(layout)
  def editingFinished(self):
    self.emit(QtCore.SIGNAL('editingFinished()'))
        
class Many2OneEditor(QtGui.QWidget):
  """Widget for editing many 2 one relations
  @param entity_admin : The Admin interface for the object on the one side of the relation
  """
  def __init__(self, entity_admin=None, parent=None):
    super(Many2OneEditor, self).__init__(parent)
    self.admin = entity_admin
    self.entity_instance_getter = None
    self.entity_set = False
    self.layout = QtGui.QHBoxLayout()
    self.layout.setSpacing(0)
    self.layout.setMargin(0)
    # Search button
    self.search_button = QtGui.QToolButton()
    self.search_button.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
    self.search_button.setAutoRaise(True)
    self.connect(self.search_button, QtCore.SIGNAL('clicked()'), self.searchButtonClicked)
    # Open button
    self.open_button = QtGui.QToolButton()
    self.open_button.setIcon(QtGui.QIcon(art.icon16('actions/document-new')))
    self.connect(self.open_button, QtCore.SIGNAL('clicked()'), self.openButtonClicked)
    self.open_button.setAutoRaise(True)  
    # Search input
    self.search_input = QtGui.QLineEdit()
    self.search_input.setReadOnly(True)
    self.connect(self.search_input, QtCore.SIGNAL('returnPressed()'), self.returnPressed)
    # Setup layout
    self.layout.addWidget(self.search_input)
    self.layout.addWidget(self.open_button)
    self.layout.addWidget(self.search_button)
    self.setLayout(self.layout)
    
  def openButtonClicked(self):
    if self.entity_set:
      return self.createFormView()
    else:
      return self.createNew()
    
  def returnPressed(self, event):
    if not self.entity_set:
      self.createSelectView()
      
  def searchButtonClicked(self):
    if self.entity_set:
      self.setEntity(lambda:None)
    else:
      self.createSelectView()
      
  def trashButtonClicked(self):
    self.setEntity(lambda:None)
    
  def createNew(self):
    from camelot.view.workspace import get_workspace, key_from_entity
    workspace = get_workspace()
    form = self.admin.createNewView(workspace)
    workspace.addWindow('new', form)
    self.connect(form, form.entity_created_signal, self.selectEntity)
    form.show()
        
  def createFormView(self):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    from camelot.view.workspace import get_workspace, key_from_entity
    if self.entity_instance_getter:
      
      def create_collection_getter(instance_getter):
        return lambda:[instance_getter()]
      
      workspace = get_workspace()  
      model = CollectionProxy(self.admin, create_collection_getter(self.entity_instance_getter), self.admin.getFields)
      form = self.admin.createFormView('', model, 0, workspace)
      workspace.addWindow(key_from_entity(self.admin.entity, 0), form)
      form.show()
    
  def setEntity(self, entity_instance_getter, propagate=True):
    
    def create_instance_getter(entity_instance):
      return lambda:entity_instance
    
    def get_instance_represenation():
      """Get a representation of the instance
      @return: (unicode, pk) its unicode representation and its primary key or ('', False) if the instance was None
      """
      entity = entity_instance_getter()
      self.entity_instance_getter = create_instance_getter(entity)
      if entity and hasattr(entity, 'id'):
        return (unicode(entity), entity.id)
      return ('', False)
    
    def set_instance_represenation(representation):
      """Update the gui"""
      desc, pk = representation
      self.search_input.setText(desc)
      if pk!=False:
        self.open_button.setIcon(QtGui.QIcon(art.icon16('places/folder')))
        self.search_button.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
        self.entity_set = True
        self.search_input.setReadOnly(True)
      else:
        self.open_button.setIcon(QtGui.QIcon(art.icon16('actions/document-new')))
        self.search_button.setIcon(QtGui.QIcon(art.icon16('actions/system-search')))
        self.entity_set = False
        self.search_input.setReadOnly(False)
      if propagate:
        self.emit(QtCore.SIGNAL('editingFinished()'))
      
    self.admin.mt.post(get_instance_represenation, set_instance_represenation)
    
  def createSelectView(self):
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()
    search_text = unicode(self.search_input.text())
    select = self.admin.createSelectView(self.admin.entity.query, parent=workspace, search_text=search_text)
    self.connect(select, select.entity_selected_signal, self.selectEntity)
    workspace.addWindow('select', select)
    select.show()
    
  def selectEntity(self, entity_instance_getter):
    self.setEntity(entity_instance_getter)
    
class One2ManyEditor(QtGui.QWidget):
  
  def __init__(self, admin=None, parent=None, create_inline=False, **kw):
    """
    @param admin: the Admin interface for the objects on the one side of the relation  
    @param create_inline: if False, then a new entity will be created within a new window, if True, it
                       will be created inline
                        
    after creating the editor, setEntityInstance needs to be called to set
    the actual data to the editor
    """
    from tableview import QueryTable
    QtGui.QWidget.__init__(self, parent)
    self.layout = QtGui.QHBoxLayout()
    self.layout.setContentsMargins(0,0,0,0)
    #
    # Setup table
    #
    self.table = QueryTable(parent)
    self.layout.addWidget(self.table) 
    self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                       QtGui.QSizePolicy.Expanding)

    self.connect(self.table.verticalHeader(),
                 QtCore.SIGNAL('sectionClicked(int)'),
                 self.createFormForIndex)

    self.admin = admin
    self.create_inline = create_inline
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    delete_button = QtGui.QToolButton()
    delete_button.setIcon(QtGui.QIcon(art.icon16('places/user-trash')))
    delete_button.setAutoRaise(True)
    self.connect(delete_button, QtCore.SIGNAL('clicked()'), self.deleteSelectedRows)
    add_button = QtGui.QToolButton()
    add_button.setIcon(QtGui.QIcon(art.icon16('actions/document-new')))
    add_button.setAutoRaise(True)
    self.connect(add_button, QtCore.SIGNAL('clicked()'), self.newRow)
    button_layout.addStretch()
    button_layout.addWidget(add_button)
    button_layout.addWidget(delete_button)      
    self.layout.addLayout(button_layout)
    self.setLayout(self.layout)
    self.model = None
  
  def setModel(self, model):
    self.model = model
    self.table.setModel(model)
    
    def create_fill_model_cache(model):
      
      def fill_model_cache():
        model._extend_cache(0, 10)
        
      return fill_model_cache
        
    def create_delegate_updater(model):
      
      def update_delegates(*args):
        self.table.setItemDelegate(model.getItemDelegate())
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeColumnsToContents()
          
      return update_delegates
      
    self.admin.mt.post(create_fill_model_cache(model), create_delegate_updater(model))
    
  def newRow(self):
    from camelot.view.workspace import get_workspace
    workspace = get_workspace()

    if self.create_inline:
      
      def create():
        o = self.admin.entity()
        self.model.insertEntityInstance(0,o)
        self.admin.setDefaults(o)
        
      self.admin.mt.post(create)
        
    else:
      form = self.admin.createNewView(workspace,
                                      oncreate=lambda o:self.model.insertEntityInstance(0,o), 
                                      onexpunge=lambda o:self.model.removeEntityInstance(o))
      workspace.addWindow('new', form)
      form.show()
    
  def deleteSelectedRows(self):
    """Delete the selected rows in this tableview"""
    logger.debug('delete selected rows called')
    for row in set(map(lambda x: x.row(), self.table.selectedIndexes())):
      self.model.removeRow(row)
          
  def createFormForIndex(self, index):
    from camelot.view.proxy.collection_proxy import CollectionProxy
    from camelot.view.workspace import get_workspace
    model = CollectionProxy(self.admin, self.model.collection_getter, self.admin.getFields, max_number_of_rows=1, edits=None)
    title = self.admin.getName()
    form = self.admin.createFormView(title, model, index, get_workspace())
    get_workspace().addWindow('createFormForIndex', form)
    form.show()

try:
  from PIL import Image as PILImage
except:
  import Image as PILImage

class ImageEditor(QtGui.QWidget):
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self.image = None 
    self.layout = QtGui.QHBoxLayout()
    #
    # Setup label
    #
    self.label = QtGui.QLabel(parent)
    self.layout.addWidget(self.label)
    self.label.setAcceptDrops(True)
#    self.draw_border()
    self.label.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
    self.label.__class__.dragEnterEvent = self.dragEnterEvent
    self.label.__class__.dragMoveEvent = self.dragEnterEvent
    self.label.__class__.dropEvent = self.dropEvent
    #
    # Setup buttons
    #
    button_layout = QtGui.QVBoxLayout()
    button_layout.setSpacing(0)
    button_layout.setMargin(0)

    file_button = QtGui.QToolButton()
    file_button.setIcon( QtGui.QIcon(art.icon16('actions/document-new')))
    file_button.setAutoRaise(True)
    file_button.setToolTip('Select image')
    self.connect(file_button, QtCore.SIGNAL('clicked()'), self.openFileDialog)
    
    app_button = QtGui.QToolButton()
    app_button.setIcon( QtGui.QIcon(art.icon16('status/folder-open')))
    app_button.setAutoRaise(True)
    app_button.setToolTip('Open image')
    self.connect(app_button, QtCore.SIGNAL('clicked()'), self.openInApp)
    
    clear_button = QtGui.QToolButton()
    clear_button.setIcon( QtGui.QIcon(art.icon16('places/user-trash')))
    clear_button.setToolTip('Clear image')
    clear_button.setAutoRaise(True)
    self.connect(clear_button, QtCore.SIGNAL('clicked()'), self.clearImage)

    vspacerItem = QtGui.QSpacerItem(20,20,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
    
    button_layout.addItem(vspacerItem)
    button_layout.addWidget(file_button)      
    button_layout.addWidget(app_button)
    button_layout.addWidget(clear_button)    

    self.layout.addLayout(button_layout)
    
    hspacerItem = QtGui.QSpacerItem(20,20,QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
    self.layout.addItem(hspacerItem)
    self.setLayout(self.layout)
    #
    # Image
    #
    self.dummy_image = os.path.normpath(art.icon32('apps/help-browser'))
    if self.image is None:
      testImage = QtGui.QImage(self.dummy_image)
      if not testImage.isNull():
        fp = open(self.dummy_image, 'rb')
        self.image = PILImage.open(fp)
        self.setPixmap(QtGui.QPixmap(self.dummy_image))
  #
  # Drag & Drop
  #
  def dragEnterEvent(self, event):
    event.acceptProposedAction()

  def dragMoveEvent(self, event):
    event.acceptProposedAction()

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      url = event.mimeData().urls()[0]
      filename = url.toLocalFile()
      if filename != '':
        self.pilimage_from_file(filename)

  #
  # Buttons methods
  #
  def clearImage(self):
    self.pilimage_from_file(self.dummy_image)
    self.draw_border()

  def openFileDialog(self):
    filter = """Image files (*.bmp *.jpg *.jpeg *.mng *.png *.pbm *.pgm *.ppm *.tiff *.xbm *.xpm)
All files (*)"""
    
    filename = QtGui.QFileDialog.getOpenFileName(self, 
                                                'Open file', 
                                                QtCore.QDir.currentPath(),
                                                filter)
    if filename != '':
      self.pilimage_from_file(filename)

  def openInApp(self):
    if self.image != None:
      tmpfp, tmpfile = tempfile.mkstemp(suffix='.png')
      self.image.save(os.fdopen(tmpfp, 'wb'), 'png')
      QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(tmpfile))

  #
  # Utils methods
  #

  def pilimage_from_file(self, filepath):
    testImage = QtGui.QImage(filepath)
    if not testImage.isNull():
      fp = open(filepath, 'rb')
      self.image = PILImage.open(fp)
      self.emit(QtCore.SIGNAL('editingFinished()'))
  
  def draw_border(self):
    self.label.setFrameShape(QtGui.QFrame.Box)
    self.label.setFrameShadow(QtGui.QFrame.Plain)
    self.label.setLineWidth(1)
    self.label.setFixedSize(100, 100)
   
  def setPixmap(self, pixmap):
    self.label.setPixmap(pixmap)      
    self.draw_border()

  def clearFirstImage(self):
    testImage = QtGui.QImage(self.dummy_image)
    if not testImage.isNull():
      fp = open(self.dummy_image, 'rb')
      self.image = PILImage.open(fp)
    self.draw_border()


class RichTextEditor(QtGui.QWidget):
  
  def __init__(self, parent=None, editable=True, **kwargs):
    QtGui.QWidget.__init__(self, parent)
    
    self.layout = QtGui.QVBoxLayout(self)
    self.layout.setSpacing(0)
    self.layout.setMargin(0)
    self.editable = editable

    #
    # Textedit
    #
    
    class CustomTextEdit(QtGui.QTextEdit):
      
      def __init__(self, parent):
        super(CustomTextEdit, self).__init__(parent)
      def focusOutEvent(self, event):
        # this seems to cause weird behaviour, where editingFinished is fired, even
        # if nothing has been edited yet
        #self.emit(QtCore.SIGNAL('editingFinished()'))
        pass
        
    self.textedit = CustomTextEdit(self)
    
    self.connect(self.textedit, QtCore.SIGNAL('editingFinished()'), self.editingFinished)
    self.textedit.setAcceptRichText(True)

    if not self.editable:
      self.textedit.setReadOnly(True)
    else:
      #
      # Buttons setup
      #
      self.toolbar = QtGui.QToolBar(self)
      self.toolbar.setContentsMargins(0,0,0,0)
      self.bold_button = QtGui.QToolButton(self)
      self.bold_button.setIcon( QtGui.QIcon(art.icon16('actions/format-text-bold')))
      self.bold_button.setAutoRaise(True)
      self.bold_button.setCheckable(True)
      self.bold_button.setMaximumSize(QtCore.QSize(20,20))
      self.bold_button.setShortcut(QtGui.QKeySequence('Ctrl+B'))
      self.connect(self.bold_button, QtCore.SIGNAL('clicked()'), self.set_bold)
      self.italic_button = QtGui.QToolButton(self)
      self.italic_button.setIcon(QtGui.QIcon(art.icon16('actions/format-text-italic')))
      self.italic_button.setAutoRaise(True)
      self.italic_button.setCheckable(True)
      self.italic_button.setMaximumSize(QtCore.QSize(20,20))
      self.italic_button.setShortcut(QtGui.QKeySequence('Ctrl+I'))
      self.connect(self.italic_button, QtCore.SIGNAL('clicked(bool)'), self.set_italic)
  
      self.underline_button = QtGui.QToolButton(self)
      self.underline_button.setIcon(QtGui.QIcon(art.icon16('actions/format-text-underline')))
      self.underline_button.setAutoRaise(True)
      self.underline_button.setCheckable(True)
      self.underline_button.setMaximumSize(QtCore.QSize(20,20))
      self.underline_button.setShortcut(QtGui.QKeySequence('Ctrl+U'))
      self.connect(self.underline_button, QtCore.SIGNAL('clicked(bool)'), self.set_underline)
  
      self.copy_button = QtGui.QToolButton(self)
      self.copy_button.setIcon(QtGui.QIcon(art.icon16('actions/edit-copy')))
      self.copy_button.setAutoRaise(True)
      self.copy_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.copy_button, QtCore.SIGNAL('clicked(bool)'), self.textedit.copy)
  
      self.cut_button = QtGui.QToolButton(self)
      self.cut_button.setIcon(QtGui.QIcon(art.icon16('actions/edit-cut')))
      self.cut_button.setAutoRaise(True)
      self.cut_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.cut_button, QtCore.SIGNAL('clicked(bool)'), self.textedit.cut)
  
      self.paste_button = QtGui.QToolButton(self)
      self.paste_button.setIcon(QtGui.QIcon(art.icon16('actions/edit-paste')))
      self.paste_button.setAutoRaise(True)
      self.paste_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.paste_button, QtCore.SIGNAL('clicked(bool)'), self.textedit.paste)
  
      self.alignleft_button = QtGui.QToolButton(self)
      self.alignleft_button.setIcon(QtGui.QIcon(art.icon16('actions/format-justify-left')))
      self.alignleft_button.setAutoRaise(True)
      self.alignleft_button.setCheckable(True)
      self.alignleft_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.alignleft_button, QtCore.SIGNAL('clicked(bool)'), self.set_alignleft)   
  
      self.aligncenter_button = QtGui.QToolButton(self)
      self.aligncenter_button.setIcon(QtGui.QIcon(art.icon16('actions/format-justify-center')))
      self.aligncenter_button.setAutoRaise(True)
      self.aligncenter_button.setCheckable(True)
      self.aligncenter_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.aligncenter_button, QtCore.SIGNAL('clicked(bool)'), self.set_aligncenter)
  
      self.alignright_button = QtGui.QToolButton(self)
      self.alignright_button.setIcon(QtGui.QIcon(art.icon16('actions/format-justify-right')))
      self.alignright_button.setAutoRaise(True)
      self.alignright_button.setCheckable(True)
      self.alignright_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.alignright_button, QtCore.SIGNAL('clicked(bool)'), self.set_alignright)
  
      self.color_button = QtGui.QToolButton(self)
      self.color_button.setAutoRaise(True)
      self.color_button.setMaximumSize(QtCore.QSize(20,20))
      self.connect(self.color_button, QtCore.SIGNAL('clicked(bool)'), self.set_color)
  
      self.toolbar.addWidget(self.copy_button)
      self.toolbar.addWidget(self.cut_button)
      self.toolbar.addWidget(self.paste_button)
      self.toolbar.addSeparator()
      self.toolbar.addWidget(self.bold_button)
      self.toolbar.addWidget(self.italic_button)      
      self.toolbar.addWidget(self.underline_button) 
      self.toolbar.addSeparator()
      self.toolbar.addWidget(self.alignleft_button)
      self.toolbar.addWidget(self.aligncenter_button)      
      self.toolbar.addWidget(self.alignright_button)   
      self.toolbar.addSeparator()
      self.toolbar.addWidget(self.color_button)   
      
      #
      # Layout
      #
      self.layout.addWidget(self.toolbar)
    self.layout.addWidget(self.textedit)
   
    self.setLayout(self.layout)
    
    #
    # Format
    #
    self.textedit.setFontWeight(QtGui.QFont.Normal)
    self.textedit.setFontItalic(False)
    self.textedit.setFontUnderline(False)
    self.textedit.setFocus(Qt.OtherFocusReason)
    self.update_alignment()

    if self.editable:
      self.connect(self.textedit, QtCore.SIGNAL('currentCharFormatChanged (const QTextCharFormat&)'), self.update_format)
      self.connect(self.textedit, QtCore.SIGNAL('cursorPositionChanged ()'), self.update_text)
    
  def editingFinished(self):
    print 'rich text editing finished'
    self.emit(QtCore.SIGNAL('editingFinished()'))
    
  #
  # Button methods
  #
  def set_bold(self):
    if self.bold_button.isChecked():
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontWeight(QtGui.QFont.Bold)
    else:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontWeight(QtGui.QFont.Normal)

  def set_italic(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontItalic(True)
    else:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontItalic(False)

  def set_underline(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontUnderline(True)
    else:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setFontUnderline(False)


  def set_alignleft(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setAlignment(Qt.AlignLeft)
    self.update_alignment(Qt.AlignLeft)

  def set_aligncenter(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setAlignment(Qt.AlignCenter)
    self.update_alignment(Qt.AlignCenter)

  def set_alignright(self, bool):
    if bool:
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setAlignment(Qt.AlignRight)
    self.update_alignment(Qt.AlignRight)

  def update_alignment(self, al=None):
    if self.editable:
      if al is None:
          al = self.textedit.alignment()
      if al == Qt.AlignLeft:
          self.alignleft_button.setChecked(True)
          self.aligncenter_button.setChecked(False)
          self.alignright_button.setChecked(False)
      elif al == Qt.AlignCenter:
          self.aligncenter_button.setChecked(True)
          self.alignleft_button.setChecked(False)
          self.alignright_button.setChecked(False)
      elif al == Qt.AlignRight:
          self.alignright_button.setChecked(True)
          self.alignleft_button.setChecked(False)
          self.aligncenter_button.setChecked(False)

  def set_color(self):
    color = QtGui.QColorDialog.getColor(self.textedit.textColor())
    if color.isValid():
      self.textedit.setFocus(Qt.OtherFocusReason)
      self.textedit.setTextColor(color)
      pixmap = QtGui.QPixmap(16,16)
      pixmap.fill(color)
      self.color_button.setIcon(QtGui.QIcon(pixmap))
  
  def update_color(self):
    if self.editable:
      color = self.textedit.textColor()
      pixmap = QtGui.QPixmap(16,16)
      pixmap.fill(color)
      self.color_button.setIcon(QtGui.QIcon(pixmap))

  def update_format(self, format):
    if self.editable:
      font = format.font()
      self.bold_button.setChecked(font.bold())
      self.italic_button.setChecked(font.italic())
      self.underline_button.setChecked(font.underline())
      self.update_alignment(self.textedit.alignment())

  def update_text(self):
    if self.editable:
      self.update_alignment()
      self.update_color()
  
  #
  # Textedit functions
  #
  def clear(self):
    self.textedit.clear()

  def setHtml(self, html):
    self.update_alignment()
    self.textedit.setHtml(html)
    self.update_color()
   
  def toHtml(self):
    return self.textedit.toHtml() 


