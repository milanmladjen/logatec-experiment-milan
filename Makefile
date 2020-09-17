#
#   Main Makefile used to build all VSNDriver projects
#

# all the directories that contain 'Makefile' under the Applications or
#  Examples subdirectory. 
# Note that we don't want infinite recursion by allowing the current directory
#  to be included in the list of directories with 'Makefile' inside
#
MAKEFILE_LIST = $(shell find Applications Examples VESNADriversDemo -name Makefile)
PROJECT_DIRS = $(dir $(MAKEFILE_LIST))
DEPLOY_LOCATION=ansible

# default target, builds all project directories
all : $(PROJECT_DIRS)

# target used for testing the 
directory_list:
	@echo
	echo "Found makefiles:"
	@echo $(MAKEFILE_LIST)
	@echo
	@echo
	echo "Makefile directories:"
	@echo $(PROJECT_DIRS)
	@echo
	@echo

# run a clean on all the project directories
clean:
	for dir in $(PROJECT_DIRS) ;         \
	  do                                 \
	    $(MAKE) --directory=$$dir clean; \
	  done;

# build one project directory; the force_look target, which is always
#   out of date, launches the build process in each directory
#
# Note: if make just enters in directory an then immediately returns with 
#  'error 2', and it doesn't give any other error message, then it might happen 
#  that
#  the files in the build directory are newer than the source files.
#  Run 'make clean' in that directory, and then it should work
#
$(PROJECT_DIRS) : force_look
	$(MAKE) --directory=$@

force_look :
	@
ci:
	#$(DEPLOY_LOCATION)/deploy_targets
	#$(DEPLOY_LOCATION)/deploy_controller
	#TODO

cd: 
	$(DEPLOY_LOCATION)/release_targets
	$(DEPLOY_LOCATION)/release_controller
	#$(DEPLOY_LOCATION)/collect_results

.PHONY: all force_look clean
