# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windows = {}

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

    def _open_window(self, window_class, window_name):
        if self.windows.get(window_name) is None:
            self.windows[window_name] = window_class()
            self.windows[window_name].destroyed.connect(lambda: self.windows.pop(window_name))
            self.windows[window_name].show()
        else:
            self.windows[window_name].activateWindow()

    def open_products_window(self):
        from app.item.ui_search_window import ItemSearchWindow
        self._open_window(ItemSearchWindow, "item_search")

    def open_supplier_search_window(self):
        from app.supplier.ui_search_window import SupplierSearchWindow
        self._open_window(SupplierSearchWindow, "supplier_search")

    def open_entry_search_window(self):
        from app.stock.ui_entry_window import StockEntryWindow
        self._open_window(StockEntryWindow, "stock_entry")

    def open_op_window(self):
        from app.production.ui_order_window import ProductionOrderWindow
        self._open_window(ProductionOrderWindow, "production_order")

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
