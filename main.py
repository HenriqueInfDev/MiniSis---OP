# main.py
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt

from app.database import get_db_manager
from app.item.ui_search_window import SearchWindow
from app.production.ui_op_window import OPWindow
from app.stock.ui_entry_search_window import EntrySearchWindow
from app.supplier.ui_supplier_search_window import SupplierSearchWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.search_window = None
        self.op_window = None
        self.entry_search_window = None
        self.supplier_search_window = None

        self.setWindowTitle("GP - MiniSis")
        self.setWindowIcon(QIcon("app/assets/logo.png"))
        self.setGeometry(100, 100, 1024, 768)

        self.setup_menus()
        self.setup_central_widget()
        self.statusBar().showMessage("Pronto")

    def setup_menus(self):
        menu_bar = self.menuBar()

        registers_menu = menu_bar.addMenu("&Cadastros")
        products_action = QAction("Produtos...", self)
        products_action.triggered.connect(self.open_products_window)
        registers_menu.addAction(products_action)

        supplier_action = QAction("Fornecedores...", self)
        supplier_action.triggered.connect(self.open_supplier_search_window)
        registers_menu.addAction(supplier_action)

        movement_menu = menu_bar.addMenu("&Movimento")
        entry_action = QAction("Entrada de Insumos...", self)
        entry_action.triggered.connect(self.open_entry_search_window)
        movement_menu.addAction(entry_action)

        op_action = QAction("Ordem de Produção...", self)
        op_action.triggered.connect(self.open_op_window)
        movement_menu.addAction(op_action)

        settings_menu = menu_bar.addMenu("&Configurações")

    def setup_central_widget(self):
        central_widget = QLabel("Bem-vindo ao MiniSis - Gestão de Produção")
        central_widget.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(central_widget)

    def open_products_window(self):
        if self.search_window is None:
            self.search_window = SearchWindow()
            self.search_window.destroyed.connect(lambda: setattr(self, 'search_window', None))
            self.search_window.show()
        else:
            self.search_window.activateWindow()
            self.search_window.raise_()

    def open_supplier_search_window(self):
        if self.supplier_search_window is None:
            self.supplier_search_window = SupplierSearchWindow()
            self.supplier_search_window.destroyed.connect(lambda: setattr(self, 'supplier_search_window', None))
            self.supplier_search_window.show()
        else:
            self.supplier_search_window.activateWindow()
            self.supplier_search_window.raise_()

    def open_op_window(self):
        if self.op_window is None:
            self.op_window = OPWindow()
            self.op_window.destroyed.connect(lambda: setattr(self, 'op_window', None))
            self.op_window.show()
        else:
            self.op_window.activateWindow()
            self.op_window.raise_()

    def open_entry_search_window(self):
        if self.entry_search_window is None:
            self.entry_search_window = EntrySearchWindow()
            self.entry_search_window.destroyed.connect(lambda: setattr(self, 'entry_search_window', None))
            self.entry_search_window.show()
        else:
            self.entry_search_window.activateWindow()
            self.entry_search_window.raise_()

def main():
    print("Inicializando o banco de dados...")
    get_db_manager()

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
