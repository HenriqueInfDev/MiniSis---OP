import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import get_db_manager
from app.item.ui_search_window import SearchWindow
from app.production.ui_op_window import OPWindow
from app.stock.ui_entry_search_window import EntrySearchWindow
from app.supplier.ui_supplier_search_window import SupplierSearchWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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
        self.products_window = SearchWindow(parent=self)
        self.products_window.setAttribute(Qt.WA_DeleteOnClose)
        self.products_window.show()

    def open_supplier_search_window(self):
        self.supplier_search_window = SupplierSearchWindow(parent=self)
        self.supplier_search_window.setAttribute(Qt.WA_DeleteOnClose)
        self.supplier_search_window.show()

    def open_op_window(self):
        self.op_window = OPWindow(parent=self)
        self.op_window.setAttribute(Qt.WA_DeleteOnClose)
        self.op_window.show()

    def open_entry_search_window(self):
        self.entry_search_window = EntrySearchWindow(parent=self)
        self.entry_search_window.setAttribute(Qt.WA_DeleteOnClose)
        self.entry_search_window.show()


def main():
    print("Inicializando o banco de dados...")
    get_db_manager()

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
