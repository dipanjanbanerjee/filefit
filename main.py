"""Start FileFit. Run with:  python main.py"""
import multiprocessing

from filefit.gui.main_window import main

if __name__ == "__main__":
    multiprocessing.freeze_support()  # needed for the frozen Windows .exe
    main()
