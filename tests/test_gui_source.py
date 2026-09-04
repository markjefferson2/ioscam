from pathlib import Path


def test_scale_initialization_does_not_fire_settings_callback_before_gui_is_built():
    source = Path("receiver/gui.py").read_text(encoding="utf-8")
    assert 'changed(str(var.get()))' not in source
    assert 'initial = float(var.get())' in source


def test_gui_does_not_install_unbraced_global_font_option():
    source = Path("receiver/gui.py").read_text(encoding="utf-8")
    assert 'option_add("*Font"' not in source
