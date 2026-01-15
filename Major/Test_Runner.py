from Simulation import *
from config import *

class simu_runner(traffic_agent):
    def __init__(self):
        super().__init__()
        
    def run_the_simulation(self):
        traci.start([sumo_binary, "-c", sumo_cfg_file])

        self.initialize_ctrl_veh_speed()
        self.initialize_sgt_ctrl_veh_speed()
        
        while self.step < simu_len:  # adjust simulation steps
            # perform one simulation step
            traci.simulationStep()
            # originally fetched all vehicle ids; now fetch controlled vehicles only
            vehicles = traci.vehicle.getIDList()
            
            self.update_vehicle_data(vehicles)
            
            self.get_ctrl_veh_speed()

            # update simulation step
            self.step += 1

        traci.close()
        
if __name__ == "__main__":
    runner = simu_runner()
    runner.run_the_simulation()
    runner.time_calculation()
    runner.visualize()
    
    


    
