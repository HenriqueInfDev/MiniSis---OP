# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.item_search_window = None
        self.supplier_search_window = None
        self.stock_entry_window = None
        self.production_order_window = None

        self.setWindowTitle("GP - MiniSis")
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
        if self.item_search_window is None:
            from app.item.ui_search_window import ItemSearchWindow
            self.item_search_window = ItemSearchWindow()
            self.item_search_window.destroyed.connect(lambda: setattr(self, 'item_search_window', None))
            self.item_search_window.show()
        else:
            self.item_search_window.activateWindow()

    def open_supplier_search_window(self):
        if self.supplier_search_window is None:
            from app.supplier.ui_search_window import SupplierSearchWindow
            self.supplier_search_window = SupplierSearchWindow()
            self.supplier_search_window.destroyed.connect(lambda: setattr(self, 'supplier_search_window', None))
            self.supplier_search_window.show()
        else:
            self.supplier_search_window.activateWindow()

    def open_entry_search_window(self):
        if self.stock_entry_window is None:
            from app.stock.ui_entry_window import StockEntryWindow
            self.stock_entry_window = StockEntryWindow()
            self.stock_entry_window.destroyed.connect(lambda: setattr(self, 'stock_entry_window', None))
            self.stock_entry_window.show()
        else:
            self.stock_entry_window.activateWindow()

    def open_op_window(self):
        if self.production_order_window is None:
            from app.production.ui_order_window import ProductionOrderWindow
            self.production_order_window = ProductionOrderWindow()
            self.production_order_window.destroyed.connect(lambda: setattr(self, 'production_order_window', None))
            self.production_order_window.show()
        else:
            self.production_order_window.activateWindow()

import logging

logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')

def main():
    try:
        logging.info("Application starting up.")
        from app.database.db import get_db_manager
        get_db_manager()
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical("Unhandled exception", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
