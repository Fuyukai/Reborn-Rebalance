import re

from rubymarshal.classes import (
    Extended,
    Module,
    RubyObject,
    RubyString,
    Symbol,
    UserDef,
    UsrMarshal,
)
from rubymarshal.constants import (
    TYPE_ARRAY,
    TYPE_BIGNUM,
    TYPE_CLASS,
    TYPE_DATA,
    TYPE_EXTENDED,
    TYPE_FALSE,
    TYPE_FIXNUM,
    TYPE_FLOAT,
    TYPE_HASH,
    TYPE_IVAR,
    TYPE_LINK,
    TYPE_MODULE,
    TYPE_NIL,
    TYPE_OBJECT,
    TYPE_REGEXP,
    TYPE_STRING,
    TYPE_STRUCT,
    TYPE_SYMBOL,
    TYPE_SYMLINK,
    TYPE_TRUE,
    TYPE_USERDEF,
    TYPE_USRMARSHAL,
)
from rubymarshal.reader import Reader


def read(self: Reader, token=None):
    if token is None:
        token = self.fd.read(1)

    # From https://docs.ruby-lang.org/en/2.1.0/marshal_rdoc.html:
    # The stream contains only one copy of each object for all objects except
    # true, false, nil, Fixnums and Symbols.
    object_index = None
    if token in (
        TYPE_IVAR,
        # TYPE_EXTENDED, TYPE_UCLASS, ????
        TYPE_CLASS,
        TYPE_MODULE,
        TYPE_FLOAT,
        TYPE_BIGNUM,
        TYPE_REGEXP,
        TYPE_ARRAY,
        TYPE_HASH,
        TYPE_STRUCT,
        TYPE_OBJECT,
        TYPE_DATA,
        TYPE_USRMARSHAL,
    ):
        self.objects.append(None)
        object_index = len(self.objects)

    result = None
    if token == TYPE_NIL:
        pass
    elif token == TYPE_TRUE:
        result = True
    elif token == TYPE_FALSE:
        result = False
    elif token == TYPE_IVAR:
        sub_token = self.fd.read(1)
        result = self.read(sub_token)
        flags: int = 0

        if sub_token == TYPE_REGEXP:
            options = ord(self.fd.read(1))
            flags = 0
            if options & 1:
                flags |= re.IGNORECASE  # type: ignore
            if options & 4:
                flags |= re.MULTILINE

        attributes = self.read_attributes()
        if sub_token in (TYPE_STRING, TYPE_REGEXP):
            encoding = self._get_encoding(attributes)
            try:
                result = result.decode(encoding)
            except UnicodeDecodeError:
                result = result.decode("unicode-escape")
        # string instance attributes are discarded
        if attributes and sub_token == TYPE_STRING:
            result = RubyString(result, attributes)
        if sub_token == TYPE_REGEXP:
            result = re.compile(str(result), flags)
        elif attributes:
            result.set_attributes(attributes)
    elif token == TYPE_STRING:
        size = self.read_long()
        result = self.fd.read(size)
    elif token == TYPE_SYMBOL:
        result = self.read_symreal()
    elif token == TYPE_FIXNUM:
        result = self.read_long()
    elif token == TYPE_ARRAY:
        num_elements = self.read_long()
        # noinspection PyUnusedLocal
        result = [self.read() for x in range(num_elements)]
    elif token == TYPE_HASH:
        num_elements = self.read_long()
        result = {}
        for _ in range(num_elements):
            key = self.read()
            value = self.read()
            result[key] = value
        result = result
    elif token == TYPE_FLOAT:
        size = self.read_long()
        floatn = self.fd.read(size)
        floatn = floatn.split(b"\0")
        result = float(floatn[0].decode("utf-8"))
    elif token == TYPE_BIGNUM:
        sign = 1 if self.fd.read(1) == b"+" else -1
        num_elements = self.read_long()
        result = 0
        factor = 1
        for _ in range(num_elements):
            result += self.read_short() * factor
            factor *= 2**16
        result *= sign
    elif token == TYPE_REGEXP:
        size = self.read_long()
        result = self.fd.read(size)
    elif token == TYPE_USRMARSHAL:
        class_symbol = self.read()
        if not isinstance(class_symbol, Symbol):
            raise ValueError("invalid class name: %r" % class_symbol)
        class_name = class_symbol.name
        attr_list = self.read()
        python_class = self.registry.get(class_name, UsrMarshal)
        if not issubclass(python_class, UsrMarshal):
            raise ValueError(
                f"invalid class mapping for {class_name!r}: {python_class!r} should be a "
                f"subclass of {UsrMarshal!r}."
            )
        result = python_class(class_name)
        result.marshal_load(attr_list)
    elif token == TYPE_SYMLINK:
        result = self.read_symlink()
    elif token == TYPE_LINK:
        link_id = self.read_long()
        if object_index and link_id >= object_index:
            raise ValueError(
                "invalid link destination: %d should be lower than %d." % (link_id, object_index)
            )

        try:
            result = self.objects[link_id]
        except IndexError:
            result = None
    elif token == TYPE_USERDEF:
        class_symbol = self.read()
        private_data = self.read(TYPE_STRING)
        if not isinstance(class_symbol, Symbol):
            raise ValueError("invalid class name: %r" % class_symbol)
        class_name = class_symbol.name
        python_class = self.registry.get(class_name, UserDef)
        if not issubclass(python_class, UserDef):
            raise ValueError(
                f"invalid class mapping for {class_name!r}: {python_class!r} should be a subclass "
                f"of {UserDef!r}."
            )
        result = python_class(class_name)
        # noinspection PyProtectedMember
        result._load(private_data)
    elif token == TYPE_MODULE:
        data = self.read(TYPE_STRING)
        module_name = data.decode()
        result = Module(module_name, None)
    elif token == TYPE_OBJECT:
        class_symbol = self.read()
        assert isinstance(class_symbol, Symbol)
        class_name = class_symbol.name
        python_class = self.registry.get(class_name, RubyObject)
        if not issubclass(python_class, RubyObject):
            raise ValueError(
                f"invalid class mapping for {class_name!r}: {python_class!r} should be a subclass "
                f"of {RubyObject!r}."
            )
        attributes = self.read_attributes()
        result = python_class(class_name, attributes)
    elif token == TYPE_EXTENDED:
        class_name = self.read(TYPE_STRING)
        result = Extended(class_name, None)
    elif token == TYPE_CLASS:
        data = self.read(TYPE_STRING)
        class_name = data.decode()
        if class_name in self.registry:
            result = self.registry[class_name]
        else:
            result = type(
                class_name.rpartition(":")[2],
                (RubyObject,),
                {"ruby_class_name": class_name},
            )
    else:
        raise ValueError("token %s is not recognized" % token)
    if object_index is not None:
        self.objects[object_index - 1] = result
    return result


def _patch():
    Reader.read = read
