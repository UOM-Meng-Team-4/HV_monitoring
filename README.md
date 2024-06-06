# HV_monitoring
This repository should be placed in the ~/ root user directory on the Jackal.

The robot will use the route.yaml file to decide the map and path it will take around the substation. you must specify the path to the map required. 

The maps should be saved in in the /maps/ folder maps scanned should be saved here using ```nav2_map_server map_saver_cli -f map_name --ros_args -r /map:=/j100_0219/map```

After a scan is completed all the data is saved in the /scans folder along with the PDF report. 
Data from Monitoring Scans
