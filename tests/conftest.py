import os

import lxml.etree
import jinja2
import pytest

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures/')
j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(FIXTURE_PATH))

@pytest.fixture
def xml_template():
    def render(tmpl_rel_path, **kwargs):
        rendered = j2_env.get_template(tmpl_rel_path).render(**kwargs)
        return lxml.etree.XML(bytes(rendered, 'utf-8'))
    return render