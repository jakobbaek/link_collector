from referals import Collector
import pandas as pd

inputfile = "/home/jakob/antivax/inputfiles/DATA AntiVax Norden_updated August.xlsx"
col = Collector(inputfile,title="test2")
col.add_services(services=["crowdtangle"])
col.add_services(services=["twitter"])
col.get_referals(running_export=False,update=False)
