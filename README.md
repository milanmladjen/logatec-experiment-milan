# LOG-a-TEC testbed

Continuous delivery template - repository for making experiments in LOG-aTEC testbed with Contiki-NG OS.

To get the repository:
```$ git clone git@github.com:logatec3/logatec-experiment.git```

To get all sub-modules files:
```$ git submodule update --init```

Do it in one step (but you will also get all nested sub-modules, which are usually useless)
```$ git clone --recurse-submodules git@github.com:logatec3/logatec-experiment.git```

**NOTE**
`Git pull` is not enough - it will only pull the changes of the base repo.
If you want to pull the changes on the sub-module as well, insert:
```$ git submodule update --remote```
You can also add `--merge` or `--rebase` to merge/rebase your branch with remote.

If you want to make some changes to sub-modules, first checkout to the branch you want, then commit changes and push them (nothing new here)

## TODO

Make few branches here --> do this on the end, when everything works

* One for SRDA devices
* One for SRDB devices
* One for LoRa

Make few more folders with examples

* /experiments/demo
* /experiments/multicast
* /experiments/neighbour-ping
* ...
