# $Id$
# 
# @Copyright@
#  				Rocks(r)
#  		         www.rocksclusters.org
#  		         version 5.4 (Maverick)
#  
# Copyright (c) 2000 - 2010 The Regents of the University of California.
# All rights reserved.	
#  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#  
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
#  
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
#  
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
# 
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of 
# the associated name, interested parties should contact Technology 
# Transfer & Intellectual Property Services, University of California, 
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910, 
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
#  
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# @Copyright@
#
# $Log$
# Revision 1.5  2011/04/14 23:08:58  anoop
# Move parallel class up one level, so that all sync commands can
# take advantage of it.
#
# Added rocks sync host sharedkey. This distributes the 411 shared key
# to compute nodes
#
# Revision 1.4  2010/09/07 23:53:03  bruno
# star power for gb
#
# Revision 1.3  2009/05/01 19:07:04  mjk
# chimi con queso
#
# Revision 1.2  2008/10/18 00:55:58  mjk
# copyright 5.1
#
# Revision 1.1  2008/08/22 23:26:38  bruno
# closer
#
#
#

import stack.commands
import threading
import subprocess
import shlex
import sys

max_threading = 512
timeout	= 30

class command(stack.commands.HostArgumentProcessor,
        stack.commands.sync.command):
	pass

class Parallel(threading.Thread):
	def __init__(self, cmd):
		self.cmd = cmd
		while threading.activeCount() > max_threading:
			time.sleep(0.001)
		threading.Thread.__init__(self)

	def run(self):
		p = subprocess.Popen(self.cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=True)
		(o, e) = p.communicate()
		if p.returncode == 0:
			sys.stdout.write(o)
		else:
			sys.stderr.write(e)
