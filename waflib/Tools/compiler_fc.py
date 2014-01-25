#!/usr/bin/env python
# encoding: utf-8

import os, sys, imp, types
from waflib import Utils, Configure, Options, Logs, Errors
from waflib.Tools import fc

fc_compiler = {
	'win32'  : ['gfortran','ifort'],
	'darwin' : ['gfortran', 'g95', 'ifort'],
	'linux'  : ['gfortran', 'g95', 'ifort'],
	'java'   : ['gfortran', 'g95', 'ifort'],
	'default': ['gfortran'],
	'aix'    : ['gfortran']
}
"""
Dict mapping the platform names to lists of names of Fortran compilers to try, in order of preference::

	from waflib.Tools.compiler_c import c_compiler
	c_compiler['linux'] = ['gfortran', 'g95', 'ifort']
"""

def __list_possible_compiler(platform):
	try:
		return fc_compiler[platform]
	except KeyError:
		return fc_compiler["default"]

def configure(conf):
	"""
	Try to find a suitable Fortran compiler or raise a :py:class:`waflib.Errors.ConfigurationError`.
	"""
	try: test_for_compiler = conf.options.check_fc
	except AttributeError: conf.fatal("Add options(opt): opt.load('compiler_fc')")
	for compiler in re.split('[ ,]+', test_for_compiler):
		conf.env.stash()
		conf.start_msg('Checking for %r (Fortran compiler)' % compiler)
		try:
			conf.load(compiler)
		except conf.errors.ConfigurationError as e:
			conf.env.revert()
			conf.end_msg(False)
			Logs.debug('compiler_fortran: %r' % e)
		else:
			if conf.env['FC']:
				conf.end_msg(conf.env.get_flat('FC'))
				conf.env.COMPILER_FORTRAN = compiler
				break
			conf.end_msg(False)
	else:
		conf.fatal('could not configure a fortran compiler!')

def options(opt):
	"""
	Restrict the compiler detection from the command-line::

		$ waf configure --check-fortran-compiler=ifort
	"""
	opt.load_special_tools('fc_*.py')
	build_platform = Utils.unversioned_sys_platform()
	possible_compiler_list = fc_compiler[build_platform in cxx_compiler and build_platform or 'default']
	test_for_compiler = ' '.join(possible_compiler_list)
	fortran_compiler_opts = opt.add_option_group('Configuration options')
	fortran_compiler_opts.add_option('--check-fortran-compiler',
			default=test_for_compiler,
			help='list of Fortran compiler to try [%s]' % test_for_compiler,
		dest="check_fc")

	for compiler in test_for_compiler.split():
		opt.load('%s' % compiler)

