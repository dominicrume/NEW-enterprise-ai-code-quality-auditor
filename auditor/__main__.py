"""Allow ``python -m auditor`` as well as the ``auditor`` command.

pip installs the console script into an environment's bin directory, which
is frequently not on a user's PATH — the most common reason a correctly
installed tool appears not to exist. ``python -m auditor`` always resolves,
because it uses the interpreter the user already named.
"""
from auditor.core.cli import main

if __name__ == "__main__":
    main()
