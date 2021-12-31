#!/usr/bin/python3

'''
Update a RootsMagic database file (v7/v8) so that anyone above a set limit of
descendant generations is set to not-living. The limit is set below.
   A list of the people being changed is printed to standard out.
Give the name of the database file as the program parameter.

Please run first on a test database or a copy of the true database.

This code is released under the MIT License: https://opensource.org/licenses/MIT
Copyright (c) 2021 John A. Andrea

Code is provided AS IS.
No support, discussion, maintenance, etc. is included or implied.
v2.1
'''

import sys
import os
import sqlite3
import datetime
import argparse


def get_program_options():
    results = dict()

    # defaults
    results['sql-out'] = False
    results['dry-run'] = False
    results['verbose'] = False
    results['max-age'] = 120
    results['max-gen'] = 4
    results['infile'] = None

    arg_help = 'Unset the living flag based on age and descendent generations.'
    parser = argparse.ArgumentParser( description=arg_help )

    parser.add_argument('infile', type=argparse.FileType('r') )

    arg_help = 'Do not change the database. Default: not selected'
    parser.add_argument( '--dry-run', action='store_true', help=arg_help )

    arg_help = 'Show everyone regardless of changes. Default: not selected'
    parser.add_argument( '--verbose', action='store_true', help=arg_help  )

    arg_help = 'Output SQL statements for the updates for later database changes.'
    parser.add_argument( '--sql-out', action='store_true', help=arg_help )

    arg_help = 'Consider anyone deceased who was born or died this many years ago.'
    arg_help += ' Default: ' + str(results['max-age'])
    parser.add_argument( '--max-age', default=results['max-age'], type=int, help=arg_help )

    arg_help = 'Consider anyone deceased who has more that this many generations of descendents.'
    arg_help += ' Default: ' + str( results['max-gen'] )
    parser.add_argument( '--max-gen', default=results['max-gen'], type=int, help=arg_help )

    args = parser.parse_args()

    results['sql-out'] = args.sql_out
    results['dry-run'] = args.dry_run
    results['verbose'] = args.verbose
    results['max-age'] = args.max_age
    results['max-gen'] = args.max_gen
    results['infile'] = args.infile.name

    # this selection forces other behaviour
    if results['sql-out']:
       results['verbose'] = False
       results['dry-run'] = True

    return results


def show_sql( p, name, count ):
    print( '' )
    print( '--', name, 'gen count', count )
    print( 'update PersonTable set Living=0 where PersonID=', p, ';' )


def change_db_flag( db_file, id_list ):
    try:
      conn = sqlite3.connect( db_file )
      cur = conn.cursor()

      sql = 'update PersonTable set Living=0 where PersonID=?'

      cur.executemany( sql, id_list )

      cur.close()
      conn.commit()

    except Exception as e:
      print( 'DBError:', e, str(e), file=sys.stderr )
    finally:
      if conn:
         conn.close()


def from_name_table( db_file ):
    data = dict()

    try:
      conn = sqlite3.connect( db_file )
      cur = conn.cursor()

      sql = 'select OwnerId, Surname, Given, BirthYear, DeathYear'
      sql += ' from NameTable'
      sql += ' where NameType = 0 and IsPrimary > 0'

      cur.execute( sql )
      for row in cur:
          data[row[0]] = { 'surname':row[1], 'given':row[2], 'birth':row[3], 'death':row[4] }

      cur.close()

    except Exception as e:
      print( 'DBError:', e, str(e), file=sys.stderr )
    finally:
      if conn:
         conn.close()

    return data


def from_family_table( db_file ):
    data = dict()

    try:
      conn = sqlite3.connect( db_file )
      cur = conn.cursor()

      sql = 'select FamilyId, FatherId, MotherId'
      sql += ' from FamilyTable'

      cur.execute( sql )
      for row in cur:
          data[row[0]] = { 'husb': row[1], 'wife': row[2], 'children': [] }

      cur.close()

      # add all the children for each family

      cur = conn.cursor()

      sql = 'select FamilyId, ChildId'
      sql += ' from ChildTable'

      cur.execute( sql )
      for row in cur:
          data[row[0]]['children'].append( row[1] )

      cur.close()

    except Exception as e:
      print( 'DBError:', e, str(e), file=sys.stderr )
    finally:
      if conn:
         conn.close()

    return data


def from_people_table( db_file ):
    data = dict()

    try:
      conn = sqlite3.connect( db_file )
      cur = conn.cursor()

      sql = 'select PersonId, Living'
      sql += ' from PersonTable'

      cur.execute( sql )
      for row in cur:
          p_id = row[0]

          data[p_id] = { 'living': row[1] }

          # additional items not from the database
          # initialize each count to None which will be tested differently than zero
          # when the counting is performed

          data[p_id]['gen-count'] = None
          data[p_id]['families'] = []
          data[p_id]['too-old'] = False

      cur.close()

    except Exception as e:
      print( 'DBError:', e, str(e), file=sys.stderr )
    finally:
      if conn:
         conn.close()

    return data


def set_child_of_family():
    # set the family links for each person
    global people
    global families

    for f in families:
        for c in families[f]['children']:
            people[c]['child-of'] = f
        for partner in ['husb','wife']:
            partner_id = families[f][partner]
            if partner_id in people:
               people[partner_id]['families'].append( f )


def count_generations( p ):
    global people
    global families

    result = 0

    for f in people[p]['families']:
        for c in families[f]['children']:
            child_count = people[c]['gen-count']
            if child_count is None:
               child_count = count_generations( c )
               people[c]['gen-count'] = child_count
            result = max( result, 1 + child_count )

    return result


def check_age( p, max_age, this_year ):
    global names

    result = False
    if p in names:
       if names[p]['death']:
          # if there is a death...
          result = True
       if not result:
          if names[p]['birth']:
             result = ( this_year - names[p]['birth'] ) > max_age

    return result


options = get_program_options()

db_file = options['infile']
if db_file.lower().endswith( '.rmgc' ) or db_file.lower().endswith( '.rmtree' ):
   if os.path.isfile( db_file ):

      this_year = datetime.datetime.now().year

      people = from_people_table( db_file )
      names = from_name_table( db_file )
      families = from_family_table( db_file )

      if options['verbose']:
         print( 'people count', len(people) )

      set_child_of_family()

      for p in people:
          if people[p]['gen-count'] is None:
             people[p]['gen-count'] = count_generations( p )
          people[p]['too-old'] = check_age( p, options['max-age'], this_year )

      # track the ids which need to be updated
      to_change = []

      for p in people:
          count = people[p]['gen-count']
          name = names[p]['surname'] + ', ' + names[p]['given']
          birth = names[p]['birth']
          death = names[p]['death']
          if birth or death:
             name += ' ('
             if birth:
                name += str(birth)
             name += '-'
             if death:
                name += str(death)
             name += ')'
          if options['verbose']:
             print( 'id', p, name, '=', count )
          if people[p]['living']:
             if count > options['max-gen'] or people[p]['too-old']:
                # needs to be a tuple for the database action
                to_change.append( (p,) )
                if options['sql-out']:
                   show_sql( p, name, count )
                else:
                   if not options['verbose']:
                      print( 'id', p, name, '=', count )
                   print( '   to be changed' )

      if not options['sql-out']:
         if options['verbose']:
            print( 'changes', len( to_change ) )
         if options['dry-run']:
            print( 'No changes - dry run' )
         else:
            if to_change:
               change_db_flag( db_file, to_change )

   else:
      print( 'File not found:', db_file, file=sys.stderr )
      sys.exit( 1 )

else:
   print( 'Given file does not match RM name types:', db_file, file=sys.stderr )
   sys.exit( 1 )
