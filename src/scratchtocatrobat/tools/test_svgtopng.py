#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
#  (<http://developer.catrobat.org/credits>)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
import imghdr
import os
import unittest

from scratchtocatrobat import common
from scratchtocatrobat import common_testing
from scratchtocatrobat.tools import svgtopng


class SvgToPngTest(common_testing.BaseTestCase):

    def test_fail_on_missing_env_variable(self):
        env_backup = None
        if svgtopng._BATIK_ENVIRONMENT_HOME in os.environ:
            env_backup = os.environ.copy()
            del os.environ[svgtopng._BATIK_ENVIRONMENT_HOME]
        try:
            svgtopng.convert("Dummy_path")
            self.fail("Expected exception not thrown")
        except common.ScratchtobatError:
            pass
        finally:
            if env_backup:
                os.environ.clear()
                os.environ.update(env_backup)
            assert svgtopng._BATIK_ENVIRONMENT_HOME in os.environ

    def test_can_convert_file_from_svg_to_png(self):
        input_svg_path = os.path.join(common.get_test_project_path("dancing_castle"), "1.svg")
        assert os.path.exists(input_svg_path)
        svgtopng.convert(input_svg_path)
        output_png_path = input_svg_path.replace(".svg", ".png")
        self.assertTrue(os.path.exists(output_png_path))
        self.assertEqual('png', imghdr.what(output_png_path))

    def test_fail_on_non_svg_input_file(self):
        try:
            svgtopng.convert(os.path.join(common.get_test_resources_path(), "83a9787d4cb6f3b7632b4ddfebf74367_pop.wav"))
            self.fail("Expected exception not thrown")
        except EnvironmentError:
            pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()