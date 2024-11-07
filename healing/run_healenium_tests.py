import sys
from PyQt5.QtWidgets import QApplication
from threading import Thread
from healenium_manager import HealeniumGUI
from healenium_pytest_integration import run_tests


def run_tests_thread():
    """Run tests in a separate thread"""
    run_tests()


def main():
    # Create PyQt application
    app = QApplication(sys.argv)

    # Create and show Healenium GUI
    gui = HealeniumGUI()
    gui.show()

    # Start test execution in separate thread
    test_thread = Thread(target=run_tests_thread)
    test_thread.daemon = True
    test_thread.start()

    # Start the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()