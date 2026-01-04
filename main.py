# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from functools import partial

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.windows = {}
        self.setWindowTitle("GP - MiniSis")
        self.setWindowIcon(QIcon('app/assets/logo.png'))
        self.setGeometry(100, 100, 1024, 768)
        self.setup_menus()
        self.setup_central_widget()
        self.statusBar().showMessage("Pronto")

    def setup_menus(self):
        menu_bar = self.menuBar()

        # Menu Cadastros
        registers_menu = menu_bar.addMenu("&Cadastros")

        from app.item.ui_search_window import ItemSearchWindow
        self._add_menu_action(registers_menu, "Produtos", "item_search_window", ItemSearchWindow)

        from app.supplier.ui_search_window import SupplierSearchWindow
        self._add_menu_action(registers_menu, "Fornecedores", "supplier_search_window", SupplierSearchWindow)

        registers_menu.addSeparator()

        from app.item.ui_unit_window import UnitWindow
        self._add_menu_action(registers_menu, "Unidades de Medida", "unit_window", UnitWindow)

        # Menu Movimento
        movement_menu = menu_bar.addMenu("&Movimento")

        from app.stock.ui_entry_search_window import EntrySearchWindow
        self._add_menu_action(movement_menu, "Entrada de Insumos", "stock_entry_window", EntrySearchWindow)

        from app.production.ui_order_window import ProductionOrderWindow
        self._add_menu_action(movement_menu, "Ordem de Produção", "production_order_window", ProductionOrderWindow)

        movement_menu.addSeparator()

        from app.sales.ui_sale_search_window import SaleSearchWindow
        self._add_menu_action(movement_menu, "Saída de Produtos", "sale_search_window", SaleSearchWindow)

        # Menu Configurações
        settings_menu = menu_bar.addMenu("&Configurações")

    def _add_menu_action(self, menu, text, window_name, window_class):
        action = QAction(text, self)
        action.triggered.connect(partial(self._open_window, window_name, window_class))
        menu.addAction(action)

    def setup_central_widget(self):
        central_widget = QLabel("Bem-vindo ao MiniSis - Gestão de Produção")
        central_widget.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(central_widget)

    def _open_window(self, window_name, window_class):
        if window_name not in self.windows or self.windows[window_name] is None:
            instance = window_class()
            self.windows[window_name] = instance
            instance.destroyed.connect(lambda: self.windows.pop(window_name, None))
            instance.show()
        else:
            self.windows[window_name].activateWindow()
            self.windows[window_name].raise_()

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
