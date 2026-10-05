from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))
from job_hunter.ui.app import main

main()
