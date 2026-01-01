# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt

from app.database import get_db_manager
from app.item.ui_search_window import SearchWindow
from app.production.ui_op_window import OPWindow
from app.stock.ui_entry_search_window import EntrySearchWindow
from app.supplier.ui_search_window import SearchSupplierWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.search_window = None
        self.op_window = None
        self.entry_search_window = None
        self.search_supplier_window = None

        self.setWindowTitle("MiniSis Gestão de Produção")
        self.setWindowIcon(QIcon("app/assets/logo.png"))
        self.setGeometry(100, 100, 1024, 768)

        self.setup_menus()
        self.setup_central_widget()
        self.statusBar().showMessage("Pronto")

    def setup_menus(self):
        menu_bar = self.menuBar()

        # Menu Cadastros
        registers_menu = menu_bar.addMenu("&Cadastros")
        products_action = QAction("Produtos...", self)
        products_action.triggered.connect(self.open_products_window)
        registers_menu.addAction(products_action)

        suppliers_action = QAction("Fornecedores...", self)
        suppliers_action.triggered.connect(self.open_supplier_window)
        registers_menu.addAction(suppliers_action)

        # Menu Movimento
        movement_menu = menu_bar.addMenu("&Movimento")
        entry_action = QAction("Entrada de Insumos...", self)
        entry_action.triggered.connect(self.open_entry_search_window)
        movement_menu.addAction(entry_action)

        op_action = QAction("Ordem de Produção...", self)
        op_action.triggered.connect(self.open_op_window)
        movement_menu.addAction(op_action)

        # Menu Configurações
        settings_menu = menu_bar.addMenu("&Configurações")

    def setup_central_widget(self):
        central_widget = QLabel("Bem-vindo ao MiniSis Gestão de Produção")
        central_widget.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(central_widget)

    def open_products_window(self):
        """Abre a janela de pesquisa de produtos, garantindo que apenas uma instância exista."""
        try:
            if self.search_window and self.search_window.isVisible():
                self.search_window.activateWindow()
                self.search_window.raise_()
                return
        except RuntimeError:
            pass

        self.search_window = SearchWindow()
        self.search_window.show()

    def open_op_window(self):
        """Abre a janela de Ordem de Produção, garantindo que apenas uma instância exista."""
        try:
            if self.op_window and self.op_window.isVisible():
                self.op_window.activateWindow()
                self.op_window.raise_()
                return
        except RuntimeError:
            pass

        self.op_window = OPWindow()
        self.op_window.show()

    def open_entry_search_window(self):
        """Abre a janela de pesquisa de entradas de insumo, garantindo que apenas uma instância exista."""
        try:
            if self.entry_search_window and self.entry_search_window.isVisible():
                self.entry_search_window.activateWindow()
                self.entry_search_window.raise_()
                return
        except RuntimeError:
            pass

        self.entry_search_window = EntrySearchWindow()
        self.entry_search_window.show()

    def open_supplier_window(self):
        """Abre a janela de pesquisa de fornecedores, garantindo que apenas uma instância exista."""
        try:
            if self.search_supplier_window and self.search_supplier_window.isVisible():
                self.search_supplier_window.activateWindow()
                self.search_supplier_window.raise_()
                return
        except RuntimeError:
            pass

        self.search_supplier_window = SearchSupplierWindow()
        self.search_supplier_window.show()

def main():
    """Função principal que inicia a aplicação."""
    print("Inicializando o banco de dados...")
    get_db_manager()

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
