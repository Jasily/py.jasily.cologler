#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 - cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import inspect
from jasily.console import ConsoleArguments
from jasily.console import MissingArgumentError

class CommandDefinitionError(Exception):
    '''user program error.'''
    def __init__(self, msg):
        super().__init__()
        self._msg = msg

    def __str__(self):
        return self._msg

class CommandRunningError(Exception):
    '''command end without finish. this Exception can safe call in command.'''
    def __init__(self, msg):
        super().__init__()
        self._msg = msg

    def __str__(self):
        return self._msg

class CommandDefinition:
    def __init__(self, func, alias):
        self._desc = func.__doc__ or '%s command.' % func.__name__
        self._func = func
        self._alias = alias
        self._enable_sorted_args = False
        self._all_args = set()
        self._args_alias = {}
        argspec = inspect.getfullargspec(func)
        if argspec[1] is None and argspec[2] is None:
            args = argspec[0]
            if len(args) < 1:
                raise CommandDefinitionError(\
                    'command must contains session as first parameter.')
            defs = argspec[3]
            if defs is None:
                self._require_args = list(args)
                self._optional_args = []
            else:
                self._require_args = args[:-len(defs)]
                self._optional_args = list(zip(args[-len(defs):], defs))
            for arg in args:
                self._all_args.add(arg)
        else:
            raise CommandDefinitionError('command cannot contains varargs or varkeywords')

    def __str__(self):
        return self.name

    @property
    def name(self):
        '''get command name.'''
        return self._func.__name__.replace('_', '-')

    def names(self):
        '''yield command name and alias.'''
        yield self.name
        for name in self.alias:
            yield name

    @property
    def alias(self):
        '''get command alias.'''
        return self._alias

    def add_arg_alias(self, arg, alias):
        assert isinstance(alias, str)
        if arg in self._all_args:
            self._args_alias.setdefault(arg, []).append(alias)
        else:
            raise KeyError

    @property
    def desc(self):
        '''get command desc.'''
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value

    @property
    def func(self):
        '''get command func pointer.'''
        return self._func

    @property
    def require_args(self):
        '''get require args.'''
        return self._require_args[1:]

    @property
    def optional_args(self):
        '''get optional args.'''
        return list(self._optional_args)

    def enable_sorted_args(self):
        self._enable_sorted_args = True

    def execute(self, session):
        '''execute command. possible raise CommandRunningError.'''

        # pre args
        assert isinstance(session, CommandSession)
        require_args = self.require_args
        optional_args = self._optional_args

        # converter
        def arg_convert(arg_name, arg_val, arg_defval):
            '''convert arg type.'''
            if arg_val == arg_defval:
                return arg_val
            if isinstance(arg_val, type(arg_defval)):
                return arg_val
            if isinstance(arg_defval, int):
                if not arg_val.isdigit():
                    raise CommandRunningError('arg %s should be digit.' % arg_name)
                return int(arg_val)
            if isinstance(arg_defval, float):
                try:
                    return float(arg_val)
                except ValueError:
                    raise CommandRunningError('arg %s should be digit.' % arg_name)
            return arg_val

        # arg func
        def get_unique_key(key):
            '''return None if key not found.'''
            exists_key = key if key in session.args else None
            if key in self._args_alias:
                alias = self._args_alias[key]
                for ali in alias:
                    if ali in session.args:
                        if exists_key is None:
                            exists_key = ali
                        else:
                            raise CommandRunningError('conflict arg flag: %s and %s' % \
                                (exists_key, ali))
            return exists_key

        def append_optional_args():
            for arg in optional_args:
                arg_name, arg_defval = arg
                exists_key = get_unique_key(arg_name)
                if exists_key is None:
                    arg_val = arg_defval
                else:
                    arg_val = session.args.get(exists_key)
                    arg_val = arg_convert(arg_name, arg_val, arg_defval)
                exe_args.append((arg[0], arg_val))

        exe_args = []
        exe_args.append((self._require_args[0], session))

        if self._enable_sorted_args:
            args_inputed = list(session.args)[2:]
            compared = len(require_args) - len(args_inputed)
            if compared > 0:
                missing = [x.upper() for x in require_args[-compared:]]
                print('error on command %s : missing argument (%s)' %\
                    (self.name, ','.join(missing)))
                return
            elif compared < 0:
                # require args
                for arg_name, arg_value in list(\
                        zip(require_args, args_inputed[-len(require_args):])):
                    exe_args.append((arg_name, arg_value))
                # optional args
                append_optional_args()
            else:
                for arg_name, arg_value in list(zip(require_args, args_inputed)):
                    exe_args.append((arg_name, arg_value))
        else:
            for key in require_args:
                arg_name = get_unique_key(key)
                if arg_name is None:
                    print('missing argument on command %s : %s' % (self.name, arg_name))
                    return
                else:
                    exe_args.append((arg_name, session.args.get_or_error(key)))
            append_optional_args()
        self.func(**dict(exe_args))

def arg_alias(**args):
    '''add arg alias to desc to command.'''
    def wrap(cmd: CommandDefinition):
        for arg in args:
            val = args[arg]
            if isinstance(val, str):
                cmd.add_arg_alias(arg, val)
            elif isinstance(val, list):
                for x in val:
                    cmd.add_arg_alias(arg, x)
            else:
                raise TypeError
        return cmd
    return wrap

def enable_sorted_args(cmd: CommandDefinition):
    '''
    if enable, will pass require args with sorted and ignore arg name.
    all optional args should before require args by input.
    the input format will be 'cmd -a -b value1 value2'.
    '''
    cmd.enable_sorted_args()
    return cmd

def desc(value):
    '''set desc to command.'''
    def wrap(cmd: CommandDefinition):
        cmd.desc = value
        return cmd
    return wrap

def command(alias=[]):
    '''make a func to a CommandDefinition object. you can manual call func by func property.'''
    def wrap(func):
        return CommandDefinition(func, alias)
    return wrap

class _CommandWrapper:
    def __init__(self, cmd):
        self.command = cmd
        self.is_enable = True

class CommandSession:
    '''parameter of @command'''
    def __init__(self, manager, args: ConsoleArguments):
        assert isinstance(manager, CommandManager)
        assert isinstance(args, ConsoleArguments)
        self._manager = manager
        self._args = args

    @property
    def command_manager(self):
        '''get caller CommandManager object.'''
        return self._manager

    @property
    def args(self) -> ConsoleArguments:
        '''get args parser for this session.'''
        return self._args

    @property
    def command(self) -> str:
        '''get command text which route to current command.'''
        return self._args[1]

class CommandManager:
    def __init__(self):
        self._commands = []
        self._commands_mapper = {}
        self._max_command_length = 0

    def register(self, cmd):
        '''register a command.'''
        wrapper = _CommandWrapper(cmd)
        self._commands.append(wrapper)
        for name in cmd.names():
            name_fixed = name.replace('_', '-')
            self._max_command_length = max(self._max_command_length, len(name_fixed))
            self._commands_mapper[name_fixed] = wrapper
        return self

    def command(self, alias=[]):
        '''create and register command.'''
        def wrap(func):
            cmd = command(alias)(func)
            self.register(cmd)
            return cmd
        return wrap

    def execute(self, argv):
        '''execute command by argv.'''
        args = ConsoleArguments(argv)
        if len(args) < 2:
            print('missing command')
            self.print_commands()
            return False
        wrapper = self._commands_mapper.get(args[1])
        if wrapper is None:
            print('unknown command: ' + args[1])
            self.print_commands()
            return False
        session = CommandSession(self, args)
        try:
            wrapper.command.execute(session)
        except CommandRunningError as err:
            print('error on command %s : %s' % (wrapper.command.name, err))
        return True

    def print_commands(self):
        print('usage:')
        for cmd in [x.command for x in self._commands if x.is_enable]:
            name = ('   ' + cmd.name).ljust(self._max_command_length) + '\t' + cmd.desc
            print(name)
            padding = ''.ljust(self._max_command_length) + '\t'
            buffer_max = 80
            formater = 'format: %s ' % cmd.name
            def build_arg_name(name):
                if name in cmd._args_alias:
                    name += '|' + '|'.join(cmd._args_alias[name])
                return name
            if len(cmd.require_args) + len(cmd.optional_args) > 0:
                list_of_optionals = []
                for name, defval in cmd.optional_args:
                    name = build_arg_name(name)
                    list_of_optionals.append('[-%s=%s]' % (name, defval))
                if len(list_of_optionals) > 0:
                    formater += ' '.join(list_of_optionals) + ' '
                if cmd._enable_sorted_args:
                    # format
                    formater += ' '.join([x.upper() for x in cmd.require_args])
                else:
                    # parameter
                    if len(cmd.require_args) > 0:
                        buffer = 'require: '
                        for arg in ['-%s' % build_arg_name(z) for z in cmd.require_args]:
                            formater += '%s=? ' % arg
                            if len(arg) + len(buffer) > buffer_max:
                                print(padding + buffer)
                                buffer = ''
                            buffer += (' ' + arg if len(buffer) > 0 else arg)
                        if len(buffer) > 0:
                            print(padding + buffer)
                            buffer = ''
                    if len(cmd.optional_args) > 0:
                        buffer = 'optional: '
                        for arg in list_of_optionals:
                            if len(arg) + len(buffer) > buffer_max:
                                print(padding + buffer)
                                buffer = ''
                            buffer += (' ' + arg if len(buffer) > 0 else arg)
                        if len(buffer) > 0:
                            print(padding + buffer)
                            buffer = ''
                    if len(cmd.alias) > 0:
                        print(' ' * 6 + 'alias: ' + ', '.join(cmd.alias))
                print(padding + formater)
            print()

