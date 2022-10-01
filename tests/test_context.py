from hm01.context import context

def test_context_usable():
    assert context.config is not None
    assert context.ikc_path is not None
    assert context.leiden_path is not None