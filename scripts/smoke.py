#!/usr/bin/env python3
"""AOS 全量烟雾测试——等同于 .claude/skills/run-aos/driver.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "skills" / "run-aos"))
from driver import main
main()
