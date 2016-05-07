
def test_import():
    """Basic sanity: import the cli module without exploding."""
    # Most of the logic happens at import time, so this isn't totally trivial.
    import ironblogger.cli
