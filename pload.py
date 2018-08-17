from __future__ import division

import os
import itertools
import collections

import numpy as np



#
#   Physical constants
#
CONST_amu  =   1.66053886e-24
CONST_mp   =   1.67262171e-24
CONST_kB   =   1.3806505e-16
CONST_pc   =   3.0856775807e18
CONST_Msun =   2.0e33

#
#    Code Units
#
UNIT_DENSITY  = CONST_mp         # proton mass
UNIT_LENGTH   = CONST_pc         # parsec
UNIT_VELOCITY = 1.0e5            # km/s
UNIT_TIME     = UNIT_LENGTH / UNIT_VELOCITY
UNIT_PRESSURE = UNIT_DENSITY * UNIT_VELOCITY**2
UNIT_ENERGY   = UNIT_PRESSURE * UNIT_LENGTH**3
UNIT_MASS     = UNIT_ENERGY / UNIT_VELOCITY**2
UNIT_MF       = np.sqrt(4.0 * np.pi * UNIT_DENSITY) * UNIT_VELOCITY
KELVIN        = UNIT_VELOCITY**2 * CONST_amu/CONST_kB

# Deprecated (read from pluto.ini instead)
gamma      =   5.0 / 3.0         # adiabatic index
mu         =   13.0 / 21.0       # mu total

time2yrs = UNIT_TIME / (365 * 24 * 3600)   # from time in code units to time in years





def process_grid_line(line):
    items = line.split()
    if len(items) == 5:  # pluto 3 grid
        return float(items[2])
    else:                # pluto 4 grid
        return (float(items[1]) + float(items[2])) / 2


def read_grid(fname):
    ''' reads grid.out
    '''
    grid = {}
    with open(fname, 'r') as fp:
        # skip comment lines
        lines = itertools.dropwhile(lambda x: x.startswith('#'), fp)
        for dim in ['x1', 'x2', 'x3']:
            npoints = int( next(lines) )
            grid[dim] = np.empty(npoints)
            for i in range(npoints):
                grid[dim][i] = process_grid_line( next(lines) )

    return grid


def write_grid_header(fname, grid, geometry):
    ''' grid header in v4 format
    '''
    keys = ['x1', 'x2', 'x3']
    ndim = sum(arr.size > 1 for arr in grid.values())

    with open(fname, 'w') as fp:
        fp.write('# ******************************************************\n')
        fp.write('# PLUTO 4.2 Grid File\n')
        fp.write('# Generated on  Mon Jul 10 10:10:10 2017\n')
        fp.write('#\n')
        fp.write('# DIMENSIONS: {}\n'.format(ndim))
        fp.write('# GEOMETRY:   {}\n'.format(geometry.upper()))
        for i in range(ndim):
            dim  = keys[i]
            nx   = grid[dim].size
            xmin, xmax = grid[dim][0], grid[dim][-1]
            fp.write('# {0} [{1:.5f},  {2:.5f}], {3} point(s), 3 ghosts\n'.format(dim.upper(), xmin, xmax, nx))
        fp.write('# ******************************************************\n')


def write_grid(fname, grid, pluto4=True, geometry='CARTESIAN'):
    '''
    '''
    if pluto4:
        write_grid_header(fname, grid, geometry)
    else:
        fp = open(fname, 'w')  # just to make sure the file is
        fp.close()             # overwritten before the following append
    with open(fname, 'a') as fp:
        for dim in ['x1', 'x2', 'x3']:
            npoints = grid[dim].size
            if npoints > 1:
                dx    = grid[dim][1] - grid[dim][0]
                left  = np.around(grid[dim] - dx / 2, 12) + 0
                right = np.around(grid[dim] + dx / 2, 12) + 0
            else:
                left  = np.array([0])
                right = np.array([1])
            fp.write("{}\n".format(npoints))
            if pluto4:
                for i in range(npoints):
                    items = (i + 1, left[i], right[i])
                    fp.write(" {}\t{:.12e}\t{:.12e}\n".format(*items))
            else:
                L, R = left, right
                for i in range(npoints):
                    items = (i + 1, L[i], 0.5*(R[i] + L[i]), R[i], R[i] - L[i])
                    fp.write(" {}\t{:.12e}\t{:.12e}\t{:.12e}\t{:.12e}\n".format(*items))


def read_output_log(fname):
    ''' reads dbl.out or flt.out
    '''
    data = {}
    with open(fname, 'r') as fp:
        for line in fp:
            items = line.split()
            nfile = int(items[0])
            time  = float(items[1])
            output_format = items[4]
            variables = items[6:]
            payload = {'time': time * time2yrs, 
                       '_time': time, 
                       '_output': output_format, 
                       'vars': variables}
            data[nfile] = payload

    return data


def read_config(fname):
    ''' reads pluto.ini
    '''
    data = collections.OrderedDict()
    with open(fname, 'r') as fp:
        for line in fp:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                section = line.lstrip('[').rstrip(']')
                data[section] = collections.OrderedDict()
            elif not line:  # skip empty line
                continue
            else:
                key, val = line.split(' ', 1)
                data[section][key] = val.strip()
    return data


def write_config(fname, data):
    ''' writes pluto.ini
    '''
    # data is OrderedDict of OrderedDicts
    with open(fname, 'w') as fp:
        for section in data:
            fp.write("[{}]\n\n".format(section))
            for key, val in data[section].items():
                fp.write("{:<25}{}\n".format(key, val))
            fp.write("\n")


