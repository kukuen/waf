#!/usr/bin/env python
# encoding: utf-8
# vim: sw=4 ts=4 noexpandtab

"""
LLVM Clang-CL support.

Clang-CL is supposed to be a drop-in replacement for MSVC CL, but also serves
well as a cross compiler for Windows from Linux (provided you have set up the
environment). Requires Visual Studio 2015+ to be installed.

On Windows it uses (most) MSVC tools.

Usage:
	$ waf configure
Or:
	$ LLVM_PATH=C:\\Program Files\\LLVM\\bin waf configure
Or:
	def configure(conf):
		conf.env.LLVM_PATH = 'C:\\Program Files\\LLVM\\bin'
		conf.load('clang_cl')
"""

import sys, os

from waflib import Utils, Errors, Logs
from waflib.Configure import conf
from waflib.Tools import msvc

def options(opt):
	msvc.options(opt)

@conf
def find_clang_cl(conf):
	"""
	Find the program clang-cl.
	"""
	del(conf.env.CC)
	del(conf.env.CXX)

	llvm_path = None

	if Utils.is_win32:
		try:
			llvm_key = Utils.winreg.OpenKey(Utils.winreg.HKEY_LOCAL_MACHINE,'SOFTWARE\\Wow6432Node\\LLVM\\LLVM')
		except OSError:
			llvm_key = Utils.winreg.OpenKey(Utils.winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\LLVM\\LLVM')

		llvm_path,type = Utils.winreg.QueryValueEx(llvm_key, '')
		llvm_path = os.path.join(llvm_path, 'bin')

	llvm_path = conf.environ.get('LLVM_PATH') or conf.env.LLVM_PATH
	if llvm_path and llvm_path != 'bin':
		paths = [llvm_path] + conf.env.PATH
	else:
		paths = conf.env.PATH

	cc = conf.find_program('clang-cl', var='CC', path_list=paths)
	conf.env.CC = conf.env.CXX = cc
	conf.env.CC_NAME_SECONDARY = conf.env.CXX_NAME_SECONDARY = 'clang'

	if not Utils.is_win32:
		conf.env.MSVC_COMPILER = 'msvc'
		conf.env.MSVC_VERSION = 19

		if not conf.env.LINK_CXX:
			conf.find_program('lld-link', path_list=paths, errmsg='lld-link was not found (linker)', var='LINK_CXX')

		if not conf.env.LINK_CC:
			conf.env.LINK_CC = conf.env.LINK_CXX

@conf
def find_llvm_tools(conf):
	"""
	Find the librarian, manifest tool, and resource compiler.
	"""
	conf.env.CC_NAME = conf.env.CXX_NAME = 'msvc'

	llvm_path = conf.environ.get('LLVM_PATH') or conf.env.LLVM_PATH
	if llvm_path and llvm_path != 'bin':
		paths = [llvm_path] + conf.env.PATH
	else:
		paths = conf.env.PATH

	if not conf.env.AR:
		stliblink = conf.find_program('llvm-lib', path_list=paths, var='AR')
		if not stliblink:
			conf.fatal('Unable to find required program "llvm-lib"')

		conf.env.ARFLAGS = ['/nologo']

	# We assume clang_cl to only be used with relatively new MSVC installations.
	conf.env.MSVC_MANIFEST = True
	conf.find_program('llvm-mt', path_list=paths, var='MT')
	conf.env.MTFLAGS = ['/nologo']

	try:
		conf.load('winres')
	except Errors.ConfigurationError:
		Logs.warn('Resource compiler not found. Compiling resource file is disabled')

def configure(conf):
	if sys.platform == 'win32':
		conf.autodetect(True)
		conf.find_msvc()
	else:
		conf.find_llvm_tools()

	conf.find_clang_cl()
	conf.msvc_common_flags()
	conf.cc_load_tools()
	conf.cxx_load_tools()
	conf.cc_add_flags()
	conf.cxx_add_flags()
	conf.link_add_flags()
	conf.visual_studio_add_flags()
