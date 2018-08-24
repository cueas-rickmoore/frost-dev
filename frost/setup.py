import os, sys
import shutil

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

EXECUTABLE = os.path.abspath(sys.executable)
EXECUTABLE_LINE = '#! '+EXECUTABLE+'\n'

PACKAGE_PATH = os.path.split(os.path.abspath(__file__))[0]
INSTALLED_PATH = EXECUTABLE.split(os.sep+'bin'+os.sep)[0]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APPLE_SCRIPTS = ( 'apple_daily_build.py',
                  'animate_apple_maps.py',
                  'build_apple_chill_grids.py',
                  'build_apple_stage_grids.py',
                  'draw_apple_chill_maps.py',
                  'draw_apple_variety_gdd_maps.py',
                  'draw_apple_variety_kill_maps.py',
                  'draw_apple_variety_stage_maps.py',
                )
APPLE_SCRIPT_DIR = os.path.join(PACKAGE_PATH, 'apple', 'scripts')

TEMP_SCRIPTS = ( 'animate_temperature_plots,py',
                 'download_latest_temp_grids.py',
                 'draw_temparature_maps.py',
                )
FROST_SCRIPT_DIR = os.path.join(PACKAGE_PATH, 'scripts')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def setExecutable(script_path):
    script = open(script_path,'r')
    first_line = script.readline()
    if first_line.startswith('#!') and 'python' in first_line:
        the_rest = script.read()
        script.close()
        msg = 'updating path to python executable in'
        print msg, script_path
        script = open(script_path,'w')
        script.write(EXECUTABLE_LINE)
        script.write(the_rest)
        script.close()
        return True
    return False

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def installScripts(dest_dirpath, script_dirpath, filenames):
    for filename in filenames:
        from_filepath = os.path.join(script_dirpath, filename)
        if os.path.exists(from_filepath):
            # eliminated compiled script
            compiled_path = from_filepath + 'c'
            if os.path.exists(compiled_path):
                os.system('rm -f %s' % compiled_path)
            # copy the script and make it executable
            dest_filepath = os.path.join(dest_dirpath, filename)
            print 'copying %s to %s' % (from_filepath, dest_filepath)
            shutil.copy(from_filepath, dest_filepath)
            os.system('chmod 755 %s' % dest_filepath)
            # change the executable
            setExecutable(dest_filepath)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

cron_dirpath = os.path.join(INSTALLED_PATH, 'cron')
if not os.path.exists(cron_dirpath): os.makedirs(cron_dirpath)
print cron_dirpath

installScripts(cron_dirpath, FROST_SCRIPT_DIR, TEMP_SCRIPTS)
installScripts(cron_dirpath, APPLE_SCRIPT_DIR, APPLE_SCRIPTS)

