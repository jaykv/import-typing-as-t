import os
import sys

from libcst.tool import main


def run():
    main(
        os.environ.get("LIBCST_TOOL_COMMAND_NAME", "libcst.tool"),
        ["codemod", "typing_as_t.codemod.ImportTypingAsCommand", "--external", "--no-format"] + sys.argv[1:],
    )
