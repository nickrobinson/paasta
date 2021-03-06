#!/usr/bin/env python
# Copyright 2015 Yelp Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains methods used by the paasta client to build a docker image."""

import os
import sys

from paasta_tools.paasta_cli.cmds.check import makefile_responds_to
from paasta_tools.paasta_cli.utils import validate_service_name
from paasta_tools.utils import _log
from paasta_tools.utils import _run
from paasta_tools.utils import get_username


def add_subparser(subparsers):
    list_parser = subparsers.add_parser(
        'cook-image',
        description='Builds a docker image',
        help='Builds a docker image')

    list_parser.add_argument('-s', '--service',
                             help='Build docker image for this service. Leading '
                                  '"services-", as included in a Jenkins job name, '
                                  'will be stripped.',
                             required=True,
                             )
    list_parser.set_defaults(command=paasta_cook_image)


def paasta_cook_image(args, service=None, soa_dir=None):
    """Build a docker image"""
    if service:
        service = service
    else:
        service = args.service
    if service and service.startswith('services-'):
        service = service.split('services-', 1)[1]
    validate_service_name(service, soa_dir)

    run_env = os.environ.copy()
    default_tag = 'paasta-cook-image-%s-%s' % (service, get_username())
    tag = run_env.get('DOCKER_TAG', default_tag)
    run_env['DOCKER_TAG'] = tag

    if not makefile_responds_to('cook-image'):
        sys.stderr.write('ERROR: local-run now requires a cook-image target to be present in the Makefile. See '
                         'http://y/paasta-contract and PAASTA-601 for more details.\n')
        sys.exit(1)

    try:
        cmd = 'make cook-image'
        returncode, output = _run(
            cmd,
            env=run_env,
            log=True,
            component='build',
            service=service,
            loglevel='debug'
        )
        if returncode != 0:
            _log(
                service=service,
                line='ERROR: make cook-image failed for %s.' % service,
                component='build',
                level='event',
            )
            sys.exit(returncode)

    except KeyboardInterrupt:
        sys.stderr.write('\nProcess interrupted by the user. Cancelling.\n')
        sys.exit(2)
