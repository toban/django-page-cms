import os
import sys
coverage_module_present = True
try:
    from coverage import coverage
except ImportError:
    coverage_module_present = False

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pages.testproj.test_settings")
current_dirname = os.path.dirname(__file__)
#sys.path.insert(0, current_dirname)
sys.path.insert(0, os.path.join(current_dirname, '..'))

from django.test.simple import DjangoTestSuiteRunner
from django.db.models import get_app, get_apps
from django.contrib.admin.sites import AlreadyRegistered
import fnmatch



# necessary for "python setup.py test"
patterns = (
    "pages.migrations.*",
    "pages.plugins.*",
    "pages.tests.*",
    "pages.testproj.*",
    "pages.urls",
    "pages.__init__",
    "pages.search_indexes",
    "pages.test_runner",
    "pages.management.commands.*",
)


def match_pattern(filename):
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False


def get_all_coverage_modules(app_module, exclude_patterns=None):
    """Returns all possible modules to report coverage on, even if they
    aren't loaded.
    """
    # We start off with the imported models.py, so we need to import
    # the parent app package to find the path.
    if exclude_patterns is None:
        exclude_patterns = []
    app_path = app_module.__name__.split('.')[:-1]
    app_package = __import__('.'.join(app_path), {}, {}, app_path[-1])
    app_dirpath = app_package.__path__[-1]

    mod_list = []
    for root, dirs, files in os.walk(app_dirpath):
        root_path = app_path + root[len(app_dirpath):].split(os.path.sep)[1:]
        for filename in files:
            if filename.lower().endswith('.py'):
                mod_name = filename[:-3].lower()
                path = '.'.join(root_path + [mod_name])
                if not match_pattern(path):
                    try:
                        mod = __import__(path, {}, {}, mod_name)
                    except ImportError as AlreadyRegistered:
                        pass
                    else:
                        mod_list.append(mod)

    return mod_list


class PageTestSuiteRunner(DjangoTestSuiteRunner):

    def run_tests(self, test_labels=('pages',), extra_tests=None):

        if coverage_module_present:
            cov = coverage()
            cov.erase()
            cov.use_cache(0)
            cov.start()
        else:
            print("No coverage support")

        results = DjangoTestSuiteRunner.run_tests(self, test_labels, extra_tests)

        if coverage_module_present:
            cov.stop()
            app = get_app('pages')
            modules = get_all_coverage_modules(app)
            cov.html_report(modules, directory='coverage')
            print('Coverage report stored in directory "coverage"')

        sys.exit(results)

def build_suite():

    runner = PageTestSuiteRunner()
    runner.setup_test_environment()
    runner.setup_databases()
    return runner.build_suite(test_labels=('pages',), extra_tests=None)


if __name__ == '__main__':
    runner = PageTestSuiteRunner(failfast=False)
    if len(sys.argv) > 1:
        runner.run_tests(test_labels=(sys.argv[1], ))
    else:
        runner.run_tests()
