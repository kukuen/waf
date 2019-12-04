#!/usr/bin/env python
# encoding: utf-8
# vim: sw=4 ts=4 noexpandtab

"""
LLVM Clang-CL support.

Clang-CL is supposed to be a drop-in replacement for MSVC CL, but also serves
well as a cross compiler for Windows from Linux (provided you have set up the
environment). Requires Visual Studio 2015+ to be installed.

On Windows it uses (most) MSVC tools.
See waflib/Tools/msvc.py and waflib/Tools/msvc_common.py for more details.

Usage:
	$ waf configure
Or:
	$ LLVM_PATH=C:\Program Files\LLVM\bin waf configure
Or:
	def configure(conf):
		conf.env.LLVM_PATH = 'C:\Program Files\LLVM\bin'
		conf.load('clang_cl')
"""

import sys, os

from waflib import Utils, Errors, Logs
from waflib.Configure import conf

def options(opt):
	from waflib.Tools.msvc import options as msvc_opt
	msvc_opt(opt)

@conf
def find_clang_cl(conf):
	"""
	Find the program clang-cl.
	"""

	v = conf.env

	del(v.CC)
	del(v.CXX)

	llvm_path = str()

	if sys.platform == 'win32':
		try:
			llvm_key = Utils.winreg.OpenKey( \
				Utils.winreg.HKEY_LOCAL_MACHINE, \
				'SOFTWARE\\Wow6432Node\\LLVM\\LLVM')
		except OSError:
			llvm_key = Utils.winreg.OpenKey( \
				Utils.winreg.HKEY_LOCAL_MACHINE, \
				'SOFTWARE\\LLVM\\LLVM')

		llvm_path,type = Utils.winreg.QueryValueEx(llvm_key, '')
		llvm_path = os.path.join(llvm_path, 'bin')

	llvm_env_path = conf.environ.get('LLVM_PATH')
	if llvm_env_path:
		llvm_path = llvm_env_path
	elif 'LLVM_PATH' in v:
		llvm_path = v['LLVM_PATH']

	paths = v.PATH
	if llvm_path != 'bin' and llvm_path != str():
		paths = [llvm_path] + v.PATH

	cc = conf.find_program('clang-cl', var='CC', path_list=paths)
	v.CC = v.CXX = cc
	v.CC_NAME_SECONDARY = v.CXX_NAME_SECONDARY = 'clang'

	if sys.platform != 'win32':
		v.MSVC_COMPILER = 'msvc'
		v.MSVC_VERSION = 19

		if not v.LINK_CXX:
			conf.find_program( \
				'lld-link', \
				path_list=paths, \
				errmsg='lld-link was not found (linker)', \
				var='LINK_CXX')

		if not v.LINK_CC:
			v.LINK_CC = v.LINK_CXX

@conf
def find_llvm_tools(conf):
	"""
	Find the librarian, manifest tool, and resource compiler.
	"""

	v = conf.env

	v.CC_NAME = v.CXX_NAME = 'msvc'

	llvm_env_path = conf.environ.get('LLVM_PATH')
	llvm_path = None
	if llvm_env_path:
		llvm_path = llvm_env_path
	elif 'LLVM_PATH' in v:
		llvm_path = v['LLVM_PATH']

	paths = v.PATH
	if llvm_path:
		paths = [llvm_path] + v.PATH

	if not v.AR:
		stliblink = conf.find_program('llvm-lib', path_list=paths, var='AR')
		if not stliblink:
			conf.fatal('Unable to find required program "llvm-lib"')

		v.ARFLAGS = ['/nologo']

	# We assume clang_cl to only be used with relatively new MSVC installations.
	v.MSVC_MANIFEST = True
	conf.find_program('llvm-mt', path_list=paths, var='MT')
	v.MTFLAGS = ['/nologo']

	try:
		conf.load('winres')
	except Errors.ConfigurationError:
		Logs.warn('Resource compiler not found. Compiling resource file is disabled')

def configure(conf):
	from waflib.Tools.msvc import autodetect, find_msvc, msvc_common_flags

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
