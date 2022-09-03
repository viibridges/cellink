#
# Class to manage the node graph construction
#
__all__ = ['registry', 'hook_parent']


class Registry(object):
    def __init__(self):
        self._lineage = dict()

    @staticmethod
    def parse_hooked_parents(parent_class_list):
        """
        @hook_parent(obj1, obj2, ...), where objX has form of the following:
            - [Class1, Class2, ...]: stack internal objects to form new nodes (quantization)
            - (Class, 2): indexing internal nodes (dequantization/collapse)
            - Class: trival
        Return:
            - formated_parent_class_list: [[(NodeClass, layer_id),(...)], [(...)]]
        """
        def _parse_layer(obj):
            if isinstance(obj, tuple):
                assert len(obj) == 2
                assert isinstance(obj[1], int) and obj[1] >= 0
                return obj
            else:
                return (obj, -1)

        def _parse_parent(obj):
            if isinstance(obj, list):
                return [_parse_layer(x) for x in obj]
            else:
                return [_parse_layer(obj)]

        formated_parent_class_list = [_parse_parent(x) for x in parent_class_list]

        return formated_parent_class_list

    def hook_parent(self, *parent_class_list):
        # register head parents to _lineage
        formated_parent_class_list = self.parse_hooked_parents(parent_class_list)
        for parents in formated_parent_class_list:
            for parent_class, _ in parents:
                if parent_class not in self._lineage:
                    self._lineage[parent_class] = []

        def class_decorator(node_class):
            # check definition duplication of node classes
            class_names = [x.__name__ for x in self._lineage]
            assert node_class.__name__ not in class_names, \
                "Class definition already exists: {}".format(node_class)
            # register class of current node
            self._lineage[node_class] = formated_parent_class_list
            return node_class
        return class_decorator

    def __getitem__(self, class_type):
        assert class_type in self._lineage, \
            "Can't find Node class in the graph: {}".format(str(class_type))
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
