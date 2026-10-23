"""Start FileFit. Run with:  python main.py   (or: python main.py --selftest)"""
import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()  # needed for the frozen Windows .exe
    if "--selftest" in sys.argv:
        from filefit.selftest import run
        sys.exit(run())
    from filefit.gui.main_window import main
    main()
