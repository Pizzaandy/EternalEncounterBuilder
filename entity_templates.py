import math
import sys
import chevron
from ebl_grammar import EblTypeError


# TODO: move entity templates to another module
class EntityTemplate:
    """
    Handles text templates to be rendered into .entities
    """
    def __init__(self, name, template, args):
        self.name = name
        self.template = template
        self.args = args
        print(f"Template {name} found")

    def modify_args(self, args):
        args = list(args)
        for i, arg in enumerate(args):
            if "[" in arg:
                clsname, clsargs = arg.split("[")
                if clsname not in [
                    cls.__name__ for cls in EntityTemplate.__subclasses__()
                ]:
                    print(f"class {clsname} not found")
                    continue
                clsargs = clsargs.replace("]", "").split()
                clsargs = [arg.strip() for arg in clsargs]
                cls = getattr(sys.modules[__name__], clsname)
                args[i] = cls().render(*clsargs)
                print(f"Rendered class {clsname} with args {clsargs}")
        return args

    def render(self, *argv) -> str:
        argv = self.modify_args(argv)
        if len(argv) != len(self.args):
            raise EblTypeError(
                f"Expected {len(self.args)} args in template {self.name}, {len(argv)} given"
            )
        t_data = {}
        for arg_name, arg in zip(self.args, argv):
            t_data[arg_name] = arg
        return chevron.render(template=self.template, data=t_data)


# noinspection PyMissingConstructor
class Vec3(EntityTemplate):
    def __init__(self):
        self.name = "Vec3"
        self.args = ["x", "y", "z"]
        self.template = """{
            x = {{x}};
            y = {{y}};
            z = {{z}};
        }
    """


def sin_cos(deg):
    rad = math.degrees(float(deg))
    return math.sin(rad), math.cos(rad)


# noinspection PyMissingConstructor
class Mat3(EntityTemplate):
    def __init__(self):
        self.name = "Mat3"
        self.args = ["x1", "y1", "z1", "x2", "y2", "z2", "x3", "y3", "z3"]
        self.template = """{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                    z = {{z1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                    z = {{z2}};
                }
                mat[2] = {
                    x = {{x3}};
                    y = {{y3}};
                    z = {{z3}};
                }
            }
        }"""

    def modify_args(self, args):
        if len(args) == 3:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(args[1])
            sr, cr = sin_cos(args[2])
            return [
                cp * cy,
                cp * sy,
                -sp,
                sr * sp * cy + cr * -sy,
                sr * sp * sy + cr * cy,
                sr * cp,
                cr * sp * cy + -sr * sy,
                cr * sp * sy + -sr * cy,
                cr * cp,
            ]
        else:
            return args


# noinspection PyMissingConstructor
class Mat2(EntityTemplate):
    def __init__(self):
        self.name = "Mat2"
        self.args = ["x1", "y1", "x2", "y2"]
        self.template = """{
            mat = {
                mat[0] = {
                    x = {{x1}};
                    y = {{y1}};
                }
                mat[1] = {
                    x = {{x2}};
                    y = {{y2}};
                }
            }
        }"""

    def modify_args(self, args):
        if len(args) == 2:
            sy, cy = sin_cos(args[0])
            sp, cp = sin_cos(args[1])
            return [cy, sy, cp, sp]
        else:
            return args
