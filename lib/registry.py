#
# Class to manage the node graph construction
#
__all__ = ['registry', 'hook_parent']

class LineageNode:
    def __init__(self):
        self.children = list()
        self.parents  = list()

class Registry(object):
    def __init__(self):
        self._lineage = dict()

        # classe names that has been registered
        # this variable is used to track class name duplications
        self._registered_classes = set()

    def hook_parent(self, *parent_class_list):
        def class_decorator(child_class):
            # check for class name duplication
            assert child_class.__name__ not in self._registered_classes, \
                "Class definition already exists: {}".format(child_class)
            self._registered_classes.add(child_class.__name__)

            # regist child_class as child class
            for parent_class in parent_class_list:
                if parent_class not in self._lineage:
                    self._lineage[parent_class] = LineageNode()
                self._lineage[parent_class].children.append(child_class)

            # regist parent_class_list as parent class
            if child_class not in self._lineage:
                self._lineage[child_class] = LineageNode()
            self._lineage[child_class].parents.extend(parent_class_list)

            return child_class

        return class_decorator

    def __getitem__(self, class_type):
        assert class_type in self._lineage, \
            "Can find NodeNode class in the graph: {}".format(str(class_type))
        return self._lineage[class_type]


class StaticModuleManager(object):
    def __init__(self):
        self._static_function_returns = dict()

    def static_initializer(self, func):
        def method_decorator(*args, **kwargs):
            func_id = id(func)
            if func_id not in self._static_function_returns:
                res = func(*args, **kwargs)
                self._static_function_returns[func_id] = res
            return self._static_function_returns[func_id]
        return method_decorator


registry = Registry()
hook_parent = registry.hook_parent

static_modules = StaticModuleManager()
static_initializer = static_modules.static_initializer
